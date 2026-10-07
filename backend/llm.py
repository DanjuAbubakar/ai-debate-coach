"""
AI provider - tries three engines in order, so the app always works:

  1. ONLINE AI  - a hosted model (default: Groq, free plan). Used when GROQ_API_KEY is set.
                  The key is set ONCE on the server; app users never see it or need one.
  2. OLLAMA     - a free model running on your own laptop. No key at all.
  3. OFFLINE    - the built-in rule-based brain (brain.py). No internet, no key.

If an engine fails (no internet, rate limit, Ollama closed...), the next one takes over.

Settings (environment variables, all optional):
  AI_MODE          auto (default) | online | ollama | offline
  GROQ_API_KEY     your Groq key - turns on the online AI
  ONLINE_AI_URL    any OpenAI-compatible endpoint (default: https://api.groq.com/openai/v1)
  ONLINE_AI_MODEL  default: openai/gpt-oss-120b
  OLLAMA_URL       default: http://localhost:11434
  OLLAMA_MODEL     default: llama3.2 (any installed model is used if this one is missing)
"""
import json
import os
import time
import urllib.error
import urllib.request

AI_MODE = os.getenv("AI_MODE", "auto").lower()

ONLINE_KEY = (os.getenv("GROQ_API_KEY") or os.getenv("ONLINE_AI_KEY") or "").strip()
ONLINE_URL = os.getenv("ONLINE_AI_URL", "https://api.groq.com/openai/v1").rstrip("/")
ONLINE_MODEL = os.getenv("ONLINE_AI_MODEL", "openai/gpt-oss-120b")
ONLINE_TIMEOUT = float(os.getenv("ONLINE_AI_TIMEOUT", "60"))
ONLINE_COOLDOWN = 60   # after a failure (e.g. rate limit), skip the online AI for a minute

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "180"))  # first reply can be slow while the model loads

_status_cache = {"checked": 0.0, "ok": False, "model": OLLAMA_MODEL}
_online_state = {"failed_at": 0.0}


# ---------------------------------------------------------------- online AI
def online_available() -> bool:
    if AI_MODE in ("offline", "ollama") or not ONLINE_KEY:
        return False
    return time.time() - _online_state["failed_at"] > ONLINE_COOLDOWN


def _online_chat(messages, json_mode=False, temperature=0.7) -> str:
    body = {"model": ONLINE_MODEL, "messages": messages, "temperature": temperature, "max_tokens": 1200}
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    req = urllib.request.Request(
        f"{ONLINE_URL}/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {ONLINE_KEY}",
                 "User-Agent": "ai-debate-coach/2.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=ONLINE_TIMEOUT) as r:
            data = json.loads(r.read().decode())
        text = (data["choices"][0]["message"].get("content") or "").strip()
        if not text:
            raise RuntimeError("empty response from online AI")
        return text
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="ignore")[:300]
        if e.code == 400 and json_mode:          # model doesn't support JSON mode: ask again without it
            return _online_chat(messages, json_mode=False, temperature=temperature)
        _online_state["failed_at"] = time.time()
        raise RuntimeError(f"Online AI error {e.code}: {detail}")
    except (urllib.error.URLError, TimeoutError, ValueError, OSError, KeyError, IndexError) as e:
        _online_state["failed_at"] = time.time()
        raise RuntimeError(f"Online AI request failed: {e}")


# ---------------------------------------------------------------- Ollama
def _choose_model(installed):
    """Use the configured model if it's installed, otherwise whatever model IS installed."""
    if not installed:
        return None
    for n in installed:                       # exact match, e.g. llama3.2:1b
        if n == OLLAMA_MODEL or n == OLLAMA_MODEL + ":latest":
            return n
    for n in installed:                       # same family, e.g. llama3.2:latest
        if n.split(":")[0] == OLLAMA_MODEL.split(":")[0]:
            return n
    return installed[0]


def ollama_available() -> bool:
    if AI_MODE in ("offline", "online"):
        return False
    if time.time() - _status_cache["checked"] < 30:
        return _status_cache["ok"]
    ok = False
    try:
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=2) as r:
            data = json.loads(r.read().decode())
            names = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
            names = [n for n in names if "embed" not in n.lower()]   # embedding models can't chat
            model = _choose_model(names)
            if model:
                _status_cache["model"] = model
                ok = True
    except Exception:
        ok = False
    _status_cache.update(checked=time.time(), ok=ok)
    return ok


def _ollama_chat(messages, json_mode=False, temperature=0.7) -> str:
    body = {"model": _status_cache["model"], "messages": messages, "stream": False,
            "options": {"temperature": temperature}}
    if json_mode:
        body["format"] = "json"
    req = urllib.request.Request(f"{OLLAMA_URL}/api/chat", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            data = json.loads(r.read().decode())
        text = data.get("message", {}).get("content", "").strip()
        if not text:
            raise RuntimeError("empty response from model")
        return text
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as e:
        _status_cache.update(checked=time.time(), ok=False)
        raise RuntimeError(f"Ollama request failed: {e}")


# ---------------------------------------------------------------- what the rest of the app uses
def ai_available() -> bool:
    """Is any real AI model (online or Ollama) reachable right now?"""
    return online_available() or ollama_available()


def active_mode() -> str:
    if online_available():
        return "online"
    if ollama_available():
        return "ollama"
    return "offline"


def current_model():
    mode = active_mode()
    if mode == "online":
        return ONLINE_MODEL
    if mode == "ollama":
        return _status_cache["model"]
    return "offline brain"


def chat(messages, json_mode=False, temperature=0.7) -> str:
    """
    Ask a real AI model: the online AI first, then Ollama.
    Raises RuntimeError if neither works, so the caller can use the offline brain instead.
    """
    errors = []
    if online_available():
        try:
            return _online_chat(messages, json_mode, temperature)
        except RuntimeError as e:
            errors.append(str(e))
    if ollama_available():
        try:
            return _ollama_chat(messages, json_mode, temperature)
        except RuntimeError as e:
            errors.append(str(e))
    raise RuntimeError("; ".join(errors) or "no AI model available")
