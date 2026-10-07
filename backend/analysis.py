"""
Simple text analysis helpers used by the offline brain and the evaluator.
No AI service needed - just plain Python.
"""
import re

STOPWORDS = set("""
a an the and or but if of to in on at for with by from as is are was were be been being this that these those
it its it's i you he she we they them our your my me us do does did not no so than then there here what which who
whom whose will would should could can may might must have has had just very also about into over more most such
only own same too any all some each few other both because while when where why how up down out off again further
once am s t don isn aren wasn weren hasn haven hadn doesn didn won wouldn shouldn couldn mustn let lets get got
""".split())

REASONING_WORDS = ["because", "therefore", "since", "thus", "so that", "as a result", "this means", "which means",
                   "consequently", "hence", "leads to", "due to", "if ", "then", "for this reason"]
EVIDENCE_WORDS = ["for example", "for instance", "such as", "according to", "research", "study", "studies",
                  "survey", "report", "data", "statistics", "evidence", "in nigeria", "in 20", "percent", "%",
                  "experience", "case of", "e.g", "shows that", "found that"]
SOURCE_WORDS = ["according to", "research", "study", "studies", "survey", "report", "published", "source",
                "world bank", "who ", "unesco", "unicef", "nbs", "statistics"]
REBUTTAL_WORDS = ["you said", "you claim", "you argued", "my opponent", "however", "but ", "on the contrary",
                  "that ignores", "that assumes", "i disagree", "not true", "that is wrong", "your point",
                  "you mentioned", "even if", "while it is true", "although"]
PERSUASION_WORDS = ["imagine", "consider", "clearly", "ultimately", "most importantly", "the real question",
                    "we must", "think about", "in conclusion", "this matters", "at the end of the day"]
CONCESSION_WORDS = ["i agree with you", "you are right", "you're right", "i concede", "you win",
                    "i change my position", "i now support your", "i switch sides"]


def words(text: str):
    return re.findall(r"[a-zA-Z']+", text.lower())


def keywords(text: str):
    return {w for w in words(text) if w not in STOPWORDS and len(w) > 2}


def sentences(text: str):
    parts = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    return [p.strip() for p in parts if len(p.strip()) > 2]


def count_hits(text: str, phrases):
    t = " " + text.lower() + " "
    return sum(1 for p in phrases if p in t)


def has_number(text: str):
    """True when the text contains a statistic-like figure (70%, 3 million, 2 out of 5) - not times like 2am."""
    t = text.lower()
    return bool(re.search(r"\d+(\.\d+)?\s*(%|percent|per cent|million|billion|thousand|out of|in every|times)", t)
                or re.search(r"\b(?!(19|20)\d{2}\b)\d{3,}\b(?!\s*(am|pm))", t))


def overlap(a: str, b: str):
    """Fraction of keywords in a that also appear in b (0-1)."""
    ka, kb = keywords(a), keywords(b)
    if not ka:
        return 0.0
    return len(ka & kb) / len(ka)


def strongest_claim(text: str):
    """Week 3 - Thursday: pick the sentence that carries the user's main claim."""
    best, best_score = None, -1
    for s in sentences(text):
        score = len(words(s)) * 0.1
        score += 2 * count_hits(s, REASONING_WORDS)
        score += 1.5 * count_hits(s, EVIDENCE_WORDS)
        score += 1 if any(w in s.lower() for w in ["should", "must", "will", "better", "worse", "harm", "benefit"]) else 0
        if score > best_score:
            best, best_score = s, score
    return best or text.strip()


def shorten(text: str, max_words: int = 22):
    w = text.split()
    return text if len(w) <= max_words else " ".join(w[:max_words]) + "..."
