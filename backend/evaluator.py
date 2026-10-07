"""
Scoring and feedback system (Week 6).

Six criteria, each scored out of 10:
logic, relevance, evidence, clarity, rebuttal_quality, persuasiveness.

The evaluator is a SEPARATE role from the debater (Week 6 Tuesday). It judges
the user's arguments only - agreeing with the AI earns no marks.

Output is structured JSON validated with Pydantic (Week 6 Wednesday).
"""
import json
import re
from typing import Dict, List

from pydantic import BaseModel, Field, field_validator

from analysis import (words, sentences, count_hits, overlap, has_number, keywords,
                      REASONING_WORDS, EVIDENCE_WORDS, SOURCE_WORDS, REBUTTAL_WORDS,
                      PERSUASION_WORDS, CONCESSION_WORDS)

CRITERIA = ["logic", "relevance", "evidence", "clarity", "rebuttal_quality", "persuasiveness"]

CRITERIA_EXPLANATIONS = {
    "logic": "Do your claims follow from your reasons? Are there gaps or contradictions?",
    "relevance": "Do your arguments stay on the motion and respond to what was said?",
    "evidence": "Do you back your claims with examples, facts or sourced data?",
    "clarity": "Are your points easy to follow - clear sentences, one idea at a time?",
    "rebuttal_quality": "Do you directly answer and weaken the opponent's arguments?",
    "persuasiveness": "Overall, how convincing is your case to a neutral listener?",
}


class Scorecard(BaseModel):
    scores: Dict[str, float]
    overall_score: float = Field(ge=0, le=10)
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    evaluator: str = "offline"

    @field_validator("scores")
    @classmethod
    def check_scores(cls, v):
        missing = [c for c in CRITERIA if c not in v]
        if missing:
            raise ValueError(f"missing criteria: {missing}")
        return {c: round(max(0.0, min(10.0, float(v[c]))), 1) for c in CRITERIA}


def _clamp(x, lo=1.0, hi=10.0):
    return round(max(lo, min(hi, x)), 1)


def heuristic_evaluate(motion: str, transcript: List[dict]) -> Scorecard:
    user_turns = [m["content"] for m in transcript if m["role"] == "user"]
    ai_turns = [m["content"] for m in transcript if m["role"] == "assistant"]

    if not user_turns:
        return Scorecard(
            scores={c: 0 for c in CRITERIA}, overall_score=0,
            strengths=["You started a debate - that's the first step."],
            weaknesses=["No arguments were submitted, so there was nothing to score."],
            recommendations=["Submit at least one argument before ending the debate."],
        )

    all_user = " ".join(user_turns)
    n = len(user_turns)
    total_words = len(words(all_user))
    avg_words = total_words / n
    sents = sentences(all_user) or [all_user]
    avg_sent_len = total_words / max(1, len(sents))

    reasoning = count_hits(all_user, REASONING_WORDS) / n
    evidence = count_hits(all_user, EVIDENCE_WORDS) / n
    sourced = count_hits(all_user, SOURCE_WORDS)
    persuasion = count_hits(all_user, PERSUASION_WORDS) / n
    conceded = count_hits(all_user, CONCESSION_WORDS) > 0

    # rebuttal: rebuttal phrases + keyword overlap with the AI turn that came just before
    rebut_overlap = []
    for i, m in enumerate(transcript):
        if m["role"] == "user":
            prev_ai = next((transcript[j]["content"] for j in range(i - 1, -1, -1)
                            if transcript[j]["role"] == "assistant"), "")
            if prev_ai:
                rebut_overlap.append(overlap(m["content"], prev_ai))
    rebut_overlap = sum(rebut_overlap) / len(rebut_overlap) if rebut_overlap else 0
    rebut_phrases = count_hits(all_user, REBUTTAL_WORDS) / n

    relevance_raw = sum(overlap(motion, u) for u in user_turns) / n  # how much of the motion is addressed
    motion_kw = keywords(motion)
    on_topic_turns = sum(1 for u in user_turns if keywords(u) & motion_kw) / n

    # repeated arguments
    repeats = sum(1 for i in range(1, n) if overlap(user_turns[i], user_turns[i - 1]) > 0.85)

    length_factor = min(1.0, avg_words / 40)  # short answers can't score highly

    logic = 3 + 3.5 * min(1, reasoning / 1.2) + 3 * length_factor - repeats
    relevance = 3 + 4 * on_topic_turns + 3 * min(1, relevance_raw * 2.5)
    ev = 2 + 4 * min(1, evidence / 1.5) + 2 * min(1, sourced / 2) + 2 * length_factor
    if has_number(all_user) and sourced == 0:
        ev -= 1  # unsourced statistics
    clarity = 9.5 - max(0, avg_sent_len - 22) * 0.25 - (3 if avg_words < 12 else 0)
    rebuttal = 2 + 3.5 * min(1, rebut_phrases / 1.5) + 4 * min(1, rebut_overlap * 3) - repeats
    persuasive = 2 + 2 * min(1, persuasion) + 0.25 * (logic + ev + rebuttal) / 3 * 4 * length_factor
    if conceded:
        rebuttal -= 2
        persuasive -= 2

    scores = {
        "logic": _clamp(logic), "relevance": _clamp(relevance), "evidence": _clamp(ev),
        "clarity": _clamp(clarity), "rebuttal_quality": _clamp(rebuttal), "persuasiveness": _clamp(persuasive),
    }
    overall = round(sum(scores.values()) / len(scores), 1)

    strengths, weaknesses, recs = [], [], []
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    for c, s in ranked[:2]:
        if s >= 6:
            strengths.append({
                "logic": "Your arguments connected claims to reasons clearly.",
                "relevance": "You stayed focused on the motion throughout.",
                "evidence": "You supported your points with examples or facts.",
                "clarity": "Your points were easy to follow.",
                "rebuttal_quality": "You engaged directly with the opponent's arguments.",
                "persuasiveness": "Your overall case was convincing.",
            }[c])
    if not strengths:
        strengths.append("You completed the debate and kept engaging with the opponent - that's how skill is built.")

    for c, s in ranked[::-1][:3]:
        if s < 6.5:
            weaknesses.append({
                "logic": "Several claims were stated without a clear reason behind them.",
                "relevance": "Some arguments drifted away from the exact motion.",
                "evidence": "Claims were rarely backed with examples or sourced facts.",
                "clarity": "Some sentences were long or hard to follow.",
                "rebuttal_quality": "You often made your own points without answering the opponent's.",
                "persuasiveness": "The case didn't fully convince - it needed stronger support and impact.",
            }[c])
            recs.append({
                "logic": "Use the pattern: claim -> 'because' -> reason -> 'this means' -> conclusion.",
                "relevance": "Re-read the motion before each turn and use its key words in your argument.",
                "evidence": "Add one concrete example per turn, and name the source of any statistic.",
                "clarity": "Keep sentences under about 20 words and make one point per paragraph.",
                "rebuttal_quality": "Begin each turn by naming the opponent's point, then explain why it fails.",
                "persuasiveness": "End each turn by explaining why your point matters most.",
            }[c])
    if repeats:
        weaknesses.append("You repeated an earlier argument instead of developing it.")
    if conceded:
        weaknesses.append("At one point you conceded your position to the opponent.")
    if not weaknesses:
        weaknesses.append("No major weaknesses - the next step is to try a harder difficulty.")
    if not recs:
        recs.append("Move up a difficulty level to keep challenging yourself.")

    return Scorecard(scores=scores, overall_score=overall, strengths=strengths,
                     weaknesses=weaknesses, recommendations=recs, evaluator="offline")


def parse_llm_scorecard(raw: str) -> Scorecard:
    """Parse JSON returned by a local LLM. Raises ValueError if it is invalid."""
    match = re.search(r"\{.*\}", raw, re.S)
    if not match:
        raise ValueError("no JSON object found")
    data = json.loads(match.group(0))
    scores = data.get("scores", data)
    scores = {k.lower().replace(" ", "_"): v for k, v in scores.items() if isinstance(v, (int, float))}
    if "rebuttal" in scores and "rebuttal_quality" not in scores:
        scores["rebuttal_quality"] = scores.pop("rebuttal")
    card = Scorecard(
        scores=scores,
        overall_score=0,
        strengths=list(data.get("strengths", []))[:4] or ["-"],
        weaknesses=list(data.get("weaknesses", []))[:4] or ["-"],
        recommendations=list(data.get("recommendations", []))[:4] or ["-"],
        evaluator="llm",
    )
    # Never trust the model's arithmetic - recompute the overall score ourselves.
    card.overall_score = round(sum(card.scores.values()) / len(card.scores), 1)
    return card
