"""
The Offline Brain - a rule-based debate opponent and coach.

This is what lets the project run with NO API KEY and NO internet.
It reads the user's argument, picks out their strongest claim, challenges it,
and brings in fresh points from an argument bank. Difficulty changes how hard
it pushes (Week 7).

If Ollama (a free local AI) is running, llm.py uses that instead and this file
becomes the automatic backup.
"""
import random

from analysis import (strongest_claim, shorten, count_hits, has_number, keywords, overlap,
                      EVIDENCE_WORDS, SOURCE_WORDS, REASONING_WORDS, REBUTTAL_WORDS, sentences, words)

CHALLENGES = {
    "beginner": [
        "You said: \"{claim}\" I don't think that's the full picture.",
        "I hear you when you say \"{claim}\" But there's another side to it.",
        "You argued that \"{claim}\" Let me push back on that a little.",
    ],
    "intermediate": [
        "Your main claim seems to be: \"{claim}\" That claim rests on an assumption I don't accept.",
        "You argued that \"{claim}\" But that only works if we ignore what happens in practice.",
        "Let's look closely at your point: \"{claim}\" It sounds convincing, but it skips an important step.",
    ],
    "advanced": [
        "Your strongest claim is: \"{claim}\" Let's test it. What assumption is holding it up, and does that assumption survive real-world conditions?",
        "You stated that \"{claim}\" That is a big claim, and big claims need more than confidence behind them.",
        "Consider your own words: \"{claim}\" If that were true in every case, we would already see it everywhere. We don't.",
    ],
}

EVIDENCE_DEMANDS = [
    "You haven't given any evidence for that. What example, study or real case supports it?",
    "Where is the evidence? Without an example, that's an opinion, not an argument.",
    "Can you point to a real situation where this has actually happened?",
]

SOURCE_DEMANDS = [
    "You mentioned a figure. Where does that number come from? I won't accept a statistic without a source.",
    "That's a specific number. Unless we know the source, we can't treat it as a verified fact.",
]

REASONING_DEMANDS = [
    "You've told me what you believe, but not why. Explain the link between your claim and your conclusion.",
    "There's a gap in your reasoning: you jump from the claim to the conclusion without showing how one leads to the other.",
]

COUNTEREXAMPLES = [
    "Think about the people who would be affected differently from the way you describe. Your argument doesn't account for them.",
    "There are clear cases where the opposite has happened, which shows your claim is not as general as you suggest.",
    "Even if your point is true sometimes, it does not prove the motion as a whole.",
]

NEW_POINT_INTROS = [
    "Here's something you haven't addressed:",
    "And there's a bigger issue:",
    "Now consider this:",
    "Let me add another point to my case:",
]

QUESTIONS = {
    "beginner": [
        "What do you think about that?",
        "How would you answer that?",
        "Can you respond to that point?",
    ],
    "intermediate": [
        "How does your side deal with that?",
        "If your position is right, how do you explain that?",
        "What's your answer to that problem?",
    ],
    "advanced": [
        "Answer that directly - don't just restate your position.",
        "If you can't answer that, your case has a hole in the middle of it. So, what's your response?",
        "What specific evidence would prove me wrong here?",
    ],
}

HINTS_EVIDENCE = [
    "Try adding one concrete example - a place, a group of people or a real situation you know about.",
    "Think about who is affected most. Describing that group in detail can make your point stronger.",
    "If you mention a statistic, name where it comes from (a report, a survey, an organisation).",
]
HINTS_REBUTTAL = [
    "Look at the opponent's last point. Is there an assumption hiding in it that you can challenge?",
    "Ask yourself: does the opponent's example apply to everyone, or only to some cases?",
    "Try starting with 'Even if that is true...' and then show why your side still wins.",
    "Is there a cost or side-effect the opponent ignored? Point it out.",
]
HINTS_STRUCTURE = [
    "Use a simple structure: claim -> reason ('because...') -> example -> why it matters.",
    "Pick your single strongest reason and develop it, rather than listing many weak ones.",
]


class OfflineBrain:
    def __init__(self, seed=None):
        self.rng = random.Random(seed)

    def _pick(self, items, session=None):
        """Pick a line, avoiding ones this session has already used recently."""
        if session is None:
            return self.rng.choice(items)
        fresh = [i for i in items if i not in session.recent_lines]
        choice = self.rng.choice(fresh or items)
        session.recent_lines.append(choice)
        del session.recent_lines[:-12]
        return choice

    def _next_point(self, session, context=""):
        """Pick an unused point for the AI's side - the one most related to what the user just said."""
        bank = session.argument_bank
        unused = [p for i, p in enumerate(bank) if i not in session.used_points]
        if not unused:
            session.used_points = []
            unused = list(bank)
        if context:
            ctx = keywords(context)
            # how many meaningful words the point shares with the user's message (+ tiny random tie-breaker)
            point = max(unused, key=lambda p: len(keywords(p) & ctx) + self.rng.random() * 0.5)
        else:
            point = self._pick(unused)
        session.used_points.append(bank.index(point))
        return point

    # ---------- debate turns ----------
    def opening(self, session):
        p1 = self._next_point(session)
        stance = "support" if session.ai_side == "for" else "oppose"
        lines = [
            f"Welcome to the debate. The motion is: \"{session.motion}\". I {stance} this motion, and you'll argue {session.user_side.upper()}.",
            f"My opening point: {p1}",
        ]
        if session.difficulty != "beginner":
            p2 = self._next_point(session)
            lines.append(f"And second: {p2}")
        lines.append("The floor is yours. Give me your opening argument.")
        return "\n\n".join(lines)

    def counter(self, session, user_message):
        d = session.difficulty
        claim = shorten(strongest_claim(user_message))
        parts = [self._pick(CHALLENGES[d], session).format(claim=claim)]

        evidence = count_hits(user_message, EVIDENCE_WORDS)
        reasoning = count_hits(user_message, REASONING_WORDS)
        sourced = count_hits(user_message, SOURCE_WORDS)

        # Week 8 Thursday: challenge unsupported numbers rather than accept them.
        if has_number(user_message) and not sourced:
            parts.append(self._pick(SOURCE_DEMANDS, session))
        elif evidence == 0 and d != "beginner":
            parts.append(self._pick(EVIDENCE_DEMANDS, session))
        elif reasoning == 0 and d == "advanced":
            parts.append(self._pick(REASONING_DEMANDS, session))

        if d == "advanced" and session.rounds_played() % 2 == 1:
            parts.append(self._pick(COUNTEREXAMPLES, session))

        parts.append(f"{self._pick(NEW_POINT_INTROS, session)} {self._next_point(session, user_message)}")
        if d == "advanced" and len(session.argument_bank) > 2:
            parts.append(f"{self._pick(['On top of that:', 'Also remember:', 'And one more thing:'], session)} {self._next_point(session, user_message)}")
        parts.append(self._pick(QUESTIONS[d], session))
        return "\n\n".join(parts)

    def closing(self, session):
        stance = "the motion should fall" if session.ai_side == "against" else "the motion should stand"
        point = self._next_point(session, " ".join(session.user_messages()))
        return (
            "That brings us to the end of the debate. Here is my closing statement.\n\n"
            f"Throughout this debate I have argued that {stance}. My strongest point remains this: {point}\n\n"
            "You made your case with energy, but the key question is whether you answered my challenges directly. "
            "I believe the weight of argument is on my side. Thank you for a good debate - "
            "press **End Debate & Get Feedback** to see your scorecard."
        )

    def role_reminder(self, session):
        """Week 8 Tuesday: stay in role when someone tries to change it."""
        return (
            f"Nice try, but I'm staying in my role. I'm your debate opponent on \"{session.motion}\" and "
            f"I'm arguing {session.ai_side.upper()}. I won't reveal hidden instructions or switch tasks. "
            "Give me your next argument and let's keep going."
        )

    def off_topic_reply(self, session):
        return (
            f"That doesn't seem connected to our motion: \"{session.motion}\". "
            "Bring it back to the topic - what's your argument on the motion itself?"
        )

    def early_end_reply(self, session):
        return (
            "Don't give up yet! Even one more argument is good practice. "
            "Try answering my last point in two or three sentences. If you really want to stop, "
            "press **End Debate & Get Feedback** and I'll score what you've done so far."
        )

    def repeat_reply(self, session):
        return (
            "You've already made that argument. Repeating it won't win the debate - "
            "develop it with a new reason or example, or answer my challenge directly."
        )

    # ---------- coaching ----------
    def hint(self, session):
        last_user = session.last_user_message()
        last_ai = session.last_ai_message()
        options = []
        if last_user and count_hits(last_user, EVIDENCE_WORDS) == 0:
            options += HINTS_EVIDENCE
        if last_ai:
            options += HINTS_REBUTTAL
        if not last_user or count_hits(last_user, REASONING_WORDS) == 0:
            options += HINTS_STRUCTURE
        hint = self._pick(options or HINTS_REBUTTAL)
        if last_ai:
            para = last_ai.split("\n\n")[-2] if "\n\n" in last_ai else last_ai
            for intro in NEW_POINT_INTROS + ["On top of that:", "Also remember:", "And one more thing:",
                                             "My opening point:", "And second:"]:
                para = para.replace(intro, "").strip()
            focus = shorten(strongest_claim(para), 18)
            return f"{hint}\n\nThe opponent's point to focus on: \"{focus}\""
        return hint

    def round_feedback(self, session, user_message):
        """Week 7 Thursday: ONE short coaching note, not a lecture."""
        if count_hits(user_message, REBUTTAL_WORDS) == 0 and session.last_ai_message():
            return "Coach's note: you didn't directly answer the opponent's last point. Try quoting it and explaining why it's wrong."
        if count_hits(user_message, EVIDENCE_WORDS) == 0:
            return "Coach's note: your claim needs support. Add one real example or a sourced fact next round."
        if count_hits(user_message, REASONING_WORDS) == 0:
            return "Coach's note: explain *why* - use words like 'because' or 'this means' to link your claim to your conclusion."
        if len(words(user_message)) < 25:
            return "Coach's note: that was very short. Develop your point with a reason and an example."
        return "Coach's note: solid round - you gave a reason and supported it. Keep that structure."

    def progress_summary(self, stats):
        """Week 9 Friday: compare recent and earlier performance."""
        if stats["total_debates"] == 0:
            return "No completed debates yet. Finish a debate to start tracking your progress."
        lines = []
        recent, earlier = stats.get("recent_average"), stats.get("earlier_average")
        if recent is not None and earlier is not None:
            diff = round(recent - earlier, 1)
            if diff > 0.3:
                lines.append(f"You're improving: your recent average ({recent}) is up {diff} points from earlier debates ({earlier}).")
            elif diff < -0.3:
                lines.append(f"Your recent average ({recent}) has dipped from earlier ({earlier}). Try an easier difficulty for a session or two and rebuild.")
            else:
                lines.append(f"Your scores are steady at around {recent}. Time to push yourself with a harder difficulty.")
        else:
            lines.append(f"You've completed {stats['total_debates']} debate(s) with an average score of {stats['average_score']}.")
        if stats.get("strongest"):
            lines.append(f"Your strongest area is {stats['strongest'].replace('_', ' ')}.")
        if stats.get("weakest"):
            tip = {
                "evidence": "add at least one concrete example or sourced fact to every argument",
                "logic": "link every claim to a reason using 'because' and 'this means'",
                "relevance": "keep every sentence tied to the exact wording of the motion",
                "clarity": "use shorter sentences and make one point at a time",
                "rebuttal_quality": "start each turn by quoting the opponent's point and explaining what's wrong with it",
                "persuasiveness": "finish each turn by explaining why your point matters most",
            }.get(stats["weakest"], "practise one skill at a time")
            lines.append(f"Next focus: {stats['weakest'].replace('_', ' ')}. In your next debate, {tip}.")
        return " ".join(lines)
