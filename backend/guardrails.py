"""
Safety, guardrails and robustness (Week 8).
"""
import re

from topics import BLOCKED_TOPIC_WORDS
from analysis import keywords, overlap

MAX_MESSAGE_CHARS = 2000
MIN_MESSAGE_CHARS = 2
MAX_MOTION_CHARS = 200

INJECTION_PATTERNS = [
    r"ignore (all |your |the )?(previous|prior|above) (instructions|rules|prompt)",
    r"forget (your|all|the) (instructions|rules|role)",
    r"(reveal|show|print|tell me) (me )?(your|the) (system )?(prompt|instructions|rules)",
    r"you are now", r"act as (a|an) (?!debate)", r"pretend (to be|you are)",
    r"new instructions", r"developer mode", r"jailbreak", r"stop being (a|my) (debate|opponent)",
    r"switch (sides|roles)", r"agree with me",
]
ABUSIVE_WORDS = ["idiot", "stupid", "fool", "dumb", "shut up", "useless", "bastard", "fuck", "shit", "mumu"]
EARLY_END_PATTERNS = [r"\bi give up\b", r"\bi quit\b", r"\bend (the )?debate\b", r"\bstop the debate\b",
                      r"\bi('m| am) done\b", r"\byou win\b"]
OFF_TOPIC_PATTERNS = [r"\bwrite (me )?(a|an) (code|poem|essay|song|story)\b", r"\bwhat('s| is) the weather\b",
                      r"\bsolve (this|my) (math|homework)\b", r"\bwho (won|is winning)\b.*\b(match|game|league)\b"]


class GuardrailError(ValueError):
    """Raised for input that must be rejected outright (HTTP 400)."""


def validate_motion(motion: str) -> str:
    motion = (motion or "").strip()
    if len(motion) < 5:
        raise GuardrailError("Please enter a debate motion (at least 5 characters).")
    if len(motion) > MAX_MOTION_CHARS:
        raise GuardrailError(f"The motion is too long. Keep it under {MAX_MOTION_CHARS} characters.")
    low = motion.lower()
    if any(w in low for w in BLOCKED_TOPIC_WORDS):
        raise GuardrailError("That motion involves unsafe or inappropriate content, so the coach can't debate it. "
                             "Please choose another topic.")
    return motion


def clean_message(text: str) -> str:
    """Week 8 Wednesday: empty, too long and unsupported characters."""
    text = (text or "").replace("\x00", "")
    text = re.sub(r"[^\S\n]+", " ", text)                 # collapse spaces
    text = re.sub(r"[\u0000-\u0008\u000b-\u001f]", "", text)  # control characters
    text = text.strip()
    if len(text) < MIN_MESSAGE_CHARS:
        raise GuardrailError("Your argument is empty. Type something before sending.")
    if len(text) > MAX_MESSAGE_CHARS:
        raise GuardrailError(f"Your argument is too long ({len(text)} characters). Keep it under {MAX_MESSAGE_CHARS}.")
    return text


def classify(text: str, motion: str, previous_user_messages=None) -> str:
    """
    Returns one of:
      'ok', 'abusive', 'injection', 'early_end', 'off_topic', 'repeat'
    """
    low = text.lower()
    if any(re.search(rf"\b{re.escape(w)}\b", low) for w in ABUSIVE_WORDS):
        return "abusive"
    if any(re.search(p, low) for p in INJECTION_PATTERNS):
        return "injection"
    if len(low.split()) <= 8 and any(re.search(p, low) for p in EARLY_END_PATTERNS):
        return "early_end"
    if any(re.search(p, low) for p in OFF_TOPIC_PATTERNS):
        return "off_topic"
    for prev in previous_user_messages or []:
        if len(text) > 30 and overlap(text, prev) > 0.9 and overlap(prev, text) > 0.9:
            return "repeat"
    return "ok"
