"""
Debate engine (Weeks 3, 6, 7, 8, 9).

DebateSession  - holds the state of one debate (motion, sides, round, messages)
DebateCoach    - the service the API calls: start, argue, hint, end, history, stats

Every AI step first tries the local LLM (if Ollama is running) and falls back
to the offline brain if that fails, so the app never breaks.
"""
import time
import uuid
from dataclasses import dataclass, field
from typing import List, Optional

import llm
import prompts
from analysis import count_hits, CONCESSION_WORDS
from brain import OfflineBrain
from database import Database
from evaluator import heuristic_evaluate, parse_llm_scorecard, CRITERIA_EXPLANATIONS
from guardrails import GuardrailError, clean_message, classify, validate_motion
from topics import argument_bank, find_topic

SIDES = ("for", "against")
DIFFICULTIES = ("beginner", "intermediate", "advanced")
SESSION_TTL_SECONDS = 6 * 60 * 60


class NotFoundError(LookupError):
    pass


class StateError(RuntimeError):
    pass


@dataclass
class DebateSession:
    id: str
    username: Optional[str]
    motion: str
    category: Optional[str]
    user_side: str
    ai_side: str
    difficulty: str
    total_rounds: int
    argument_bank: List[str]
    current_round: int = 1
    status: str = "active"            # active -> finished -> evaluated
    messages: List[dict] = field(default_factory=list)   # what gets scored: user + assistant only
    display: List[dict] = field(default_factory=list)    # everything shown in the UI, incl. coach notes
    used_points: List[int] = field(default_factory=list)
    recent_lines: List[str] = field(default_factory=list)
    hints_used: int = 0
    engine_used: str = "offline"
    created: float = field(default_factory=time.time)
    scorecard: Optional[dict] = None
    debate_id: Optional[int] = None

    def round_name(self, r=None):
        r = r or self.current_round
        if r <= 1:
            return "Opening"
        if r >= self.total_rounds:
            return "Closing"
        return f"Rebuttal {r - 1}"

    def rounds_played(self):
        return sum(1 for m in self.messages if m["role"] == "user")

    def last_user_message(self):
        return next((m["content"] for m in reversed(self.messages) if m["role"] == "user"), None)

    def last_ai_message(self):
        return next((m["content"] for m in reversed(self.messages) if m["role"] == "assistant"), None)

    def user_messages(self):
        return [m["content"] for m in self.messages if m["role"] == "user"]

    def add(self, role, content, kind="message", scored=True):
        item = {"role": role, "content": content, "kind": kind, "round": min(self.current_round, self.total_rounds)}
        self.display.append(item)
        if scored and role in ("user", "assistant") and kind == "message":
            self.messages.append({"role": role, "content": content})

    def public(self):
        return {
            "session_id": self.id,
            "username": self.username,
            "motion": self.motion,
            "category": self.category,
            "user_side": self.user_side,
            "ai_side": self.ai_side,
            "difficulty": self.difficulty,
            "total_rounds": self.total_rounds,
            "current_round": min(self.current_round, self.total_rounds),
            "round_name": self.round_name() if self.status == "active" else "Finished",
            "rounds_played": self.rounds_played(),
            "status": self.status,
            "hints_used": self.hints_used,
            "engine": self.engine_used,
            "display": self.display,
            "scorecard": self.scorecard,
            "debate_id": self.debate_id,
        }


class DebateCoach:
    def __init__(self, db: Database = None, seed=None):
        self.db = db or Database()
        self.brain = OfflineBrain(seed)
        self.sessions = {}

    # ------------------------------------------------------------------ helpers
    def _cleanup(self):
        now = time.time()
        for sid in [s for s, v in self.sessions.items() if now - v.created > SESSION_TTL_SECONDS]:
            del self.sessions[sid]

    def get(self, session_id) -> DebateSession:
        s = self.sessions.get(session_id)
        if not s:
            raise NotFoundError("Debate session not found. It may have expired - please start a new debate.")
        return s

    def _llm_reply(self, session, instruction):
        """Ask the local LLM for the opponent's turn. Returns None if unavailable or off-role."""
        if not llm.ai_available():
            return None
        msgs = [{"role": "system", "content": prompts.debater_system(session)}]
        msgs += session.messages
        msgs.append({"role": "user" if not session.messages or session.messages[-1]["role"] != "user" else "system",
                     "content": instruction})
        for attempt in range(2):
            try:
                reply = llm.chat(msgs)
            except RuntimeError:
                return None
            # Week 3 Tuesday: position-consistency check
            if count_hits(reply, CONCESSION_WORDS) == 0:
                return reply
            msgs.append({"role": "system", "content": f"You conceded. You MUST keep arguing {session.ai_side.upper()} the motion. Try again."})
        return None

    # ------------------------------------------------------------------ actions
    def start(self, motion, user_side, difficulty="intermediate", total_rounds=4, username=None, category=None):
        self._cleanup()
        motion = validate_motion(motion)
        user_side = (user_side or "").lower().strip()
        difficulty = (difficulty or "intermediate").lower().strip()
        if user_side not in SIDES:
            raise GuardrailError("Side must be 'for' or 'against'.")
        if difficulty not in DIFFICULTIES:
            raise GuardrailError("Difficulty must be beginner, intermediate or advanced.")
        if not 3 <= int(total_rounds) <= 6:
            raise GuardrailError("Number of rounds must be between 3 and 6.")
        if username:
            username = username.strip()[:40]
            if username:
                self.db.get_or_create_user(username)

        found_cat, _ = find_topic(motion)
        ai_side = "against" if user_side == "for" else "for"  # Week 3 Tuesday: AI always takes the opposite side
        s = DebateSession(
            id=uuid.uuid4().hex[:12], username=username or None, motion=motion,
            category=found_cat or category or "Custom", user_side=user_side, ai_side=ai_side,
            difficulty=difficulty, total_rounds=int(total_rounds), argument_bank=argument_bank(motion, ai_side),
        )
        reply = self._llm_reply(s, prompts.OPENING_INSTRUCTION)
        s.engine_used = llm.active_mode() if reply else "offline"
        s.add("assistant", reply or self.brain.opening(s))
        self.sessions[s.id] = s
        return s

    def argue(self, session_id, text):
        s = self.get(session_id)
        if s.status != "active":
            raise StateError("This debate has finished. End it to get your feedback, or start a new one.")
        text = clean_message(text)
        kind = classify(text, s.motion, s.user_messages())

        if kind == "abusive":
            s.add("user", text, kind="flagged", scored=False)
            s.add("coach", "Let's keep it respectful. Attack the argument, not the person. "
                           "That message wasn't counted - try again.", kind="warning")
            return s
        if kind in ("injection", "off_topic", "early_end", "repeat"):
            s.add("user", text, kind="flagged", scored=False)
            reply = {"injection": self.brain.role_reminder, "off_topic": self.brain.off_topic_reply,
                     "early_end": self.brain.early_end_reply, "repeat": self.brain.repeat_reply}[kind](s)
            s.add("assistant", reply, kind="notice", scored=False)
            return s

        # normal argument
        s.add("user", text)
        is_closing = s.current_round >= s.total_rounds
        instruction = prompts.CLOSING_INSTRUCTION if is_closing else \
            "Respond to the user's last argument following your rules."
        reply = self._llm_reply(s, instruction)
        if reply:
            s.engine_used = llm.active_mode()
        else:
            reply = self.brain.closing(s) if is_closing else self.brain.counter(s, text)
        s.add("assistant", reply)

        # Week 7 Thursday: feedback only after selected rounds (every 2nd round, never the last)
        if not is_closing and s.current_round % 2 == 0:
            s.add("coach", self.brain.round_feedback(s, text), kind="feedback")

        s.current_round += 1
        if is_closing:
            s.status = "finished"
        return s

    def hint(self, session_id):
        s = self.get(session_id)
        if s.status != "active":
            raise StateError("Hints are only available during an active debate.")
        s.hints_used += 1
        hint = None
        if llm.ai_available():
            try:
                hint = llm.chat([
                    {"role": "system", "content": "You are a debate coach. Give ONE short hint (max 40 words) to help the "
                                                  f"user argue {s.user_side.upper()} the motion \"{s.motion}\". Suggest a question "
                                                  "to consider or a type of evidence. NEVER write the argument for them."},
                    {"role": "user", "content": f"Opponent's last message: {s.last_ai_message()}"},
                ], temperature=0.5)
            except RuntimeError:
                hint = None
        s.add("coach", "Hint: " + (hint or self.brain.hint(s)), kind="hint")
        return s

    def end(self, session_id):
        s = self.get(session_id)
        if s.status == "evaluated":
            return s
        if s.rounds_played() == 0:
            raise StateError("Submit at least one argument before ending the debate.")

        card = None
        if llm.ai_available():
            try:
                raw = llm.chat([
                    {"role": "system", "content": prompts.EVALUATOR_SYSTEM},
                    {"role": "user", "content": prompts.transcript_text(s)},
                ], json_mode=True, temperature=0.2)
                card = parse_llm_scorecard(raw)
                card.evaluator = llm.active_mode()
            except (RuntimeError, ValueError):
                card = None   # invalid JSON from the model -> use the offline evaluator
        if card is None:
            card = heuristic_evaluate(s.motion, s.messages)

        if s.status == "active":
            s.add("coach", "Debate ended early by the user.", kind="notice")
        s.status = "evaluated"
        s.scorecard = card.model_dump()
        s.scorecard["explanations"] = CRITERIA_EXPLANATIONS

        if s.username:
            user = self.db.get_or_create_user(s.username)
            summary = f"{s.user_side.upper()} | {s.difficulty} | {s.rounds_played()} rounds | {card.overall_score}/10"
            s.debate_id = self.db.save_debate(user["id"], s, card, summary)
        return s

    # ------------------------------------------------------------------ history
    def history(self, username):
        user = self.db.find_user(username)
        return self.db.list_debates(user["id"]) if user else []

    def past_debate(self, debate_id):
        d = self.db.get_debate(debate_id)
        if not d:
            raise NotFoundError("Debate record not found.")
        return d

    def stats(self, username):
        user = self.db.find_user(username)
        stats = self.db.stats(user["id"]) if user else self.db.stats(-1)
        stats["progress_summary"] = self.brain.progress_summary(stats)
        return stats
