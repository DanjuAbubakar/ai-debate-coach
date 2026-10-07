"""
Look and feel for AI Debate Coach - "The Chamber".

The design borrows from real debating: a motion is read as "This House believes that...",
two benches face each other (green FOR, red AGAINST), and a judge fills in a scoresheet.

  ink      #16213E  text, sidebar, buttons
  paper    #F5F7FA  page background
  for      #1C7C54  the FOR bench
  against  #B3263E  the AGAINST bench
  gold     #E3A72F  scores only (the gavel)

Fonts: Bricolage Grotesque (headings) + Atkinson Hyperlegible (body, very readable on phones).
If there's no internet (e.g. offline demo), the browser's normal sans-serif font is used instead.
"""
from html import escape

SIDE_COLORS = {"for": "#1C7C54", "against": "#B3263E"}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700;12..96,800&display=swap');

:root {
  --ink: #16213E; --ink-soft: #2A3657; --paper: #F5F7FA; --line: #DCE2EB; --muted: #5A6478;
  --for: #1C7C54; --for-tint: #E7F3ED; --against: #B3263E; --against-tint: #F8E9EC;
  --gold: #E3A72F; --gold-tint: #FBF2DE;
  --display: 'Bricolage Grotesque', 'Segoe UI', system-ui, sans-serif;
  --body: 'Atkinson Hyperlegible', 'Segoe UI', system-ui, sans-serif;
}

/* ---------- base ---------- */
html, body, [data-testid="stAppViewContainer"], .stMarkdown, .stMarkdown p, .stMarkdown li,
label, input, textarea, button, [data-testid="stWidgetLabel"] { font-family: var(--body); }
[data-testid="stAppViewContainer"] { background: var(--paper); color: var(--ink); }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stDecoration"], footer { display: none; }
.block-container { padding-top: 2.2rem; padding-bottom: 4rem; max-width: 1080px; }
h1, h2, h3, h4 { font-family: var(--display) !important; color: var(--ink); letter-spacing: -0.02em; }
h1 { font-weight: 800 !important; }
h2, h3 { font-weight: 700 !important; }
a { color: var(--for); }

/* ---------- buttons & inputs ---------- */
.stButton > button, .stFormSubmitButton > button {
  border-radius: 10px; font-weight: 700; padding: 0.55rem 1.15rem; border: 1.5px solid var(--ink);
  transition: transform .08s ease;
}
.stFormSubmitButton > button, [data-testid="stColumn"] .stButton > button,
[data-testid="column"] .stButton > button { width: 100%; }
.stButton > button:active, .stFormSubmitButton > button:active { transform: translateY(1px); }
.stButton > button:focus-visible, .stFormSubmitButton > button:focus-visible {
  outline: 3px solid var(--gold); outline-offset: 2px;
}
[data-baseweb="input"], [data-baseweb="select"] > div, [data-baseweb="textarea"] {
  border-radius: 10px !important; border: 1px solid #C9D1DD !important; background: #F5F7FA !important; }
[data-baseweb="input"]:focus-within, [data-baseweb="textarea"]:focus-within { border-color: var(--ink) !important; }
[data-baseweb="input"] input, [data-baseweb="textarea"] textarea { background: transparent !important; }
[data-testid="stForm"] { background: #fff; border: 1px solid var(--line); border-radius: 16px; padding: 1.4rem 1.4rem 1rem; }
.stTabs [data-baseweb="tab-list"] { gap: 0.25rem; }
.stTabs [data-baseweb="tab"] { font-family: var(--display); font-weight: 700; font-size: 1.02rem; }

/* ---------- sidebar ---------- */
[data-testid="stSidebar"] { background: var(--ink); }
[data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span,
[data-testid="stSidebar"] div { color: #E6EAF2; }
[data-testid="stSidebar"] [role="radiogroup"] { gap: 2px; }
[data-testid="stSidebar"] [role="radiogroup"] label {
  width: 100%; padding: 0.6rem 0.8rem; border-radius: 8px; margin: 0; cursor: pointer;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover { background: rgba(255,255,255,0.06); }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
  background: rgba(255,255,255,0.10); box-shadow: inset 3px 0 0 var(--gold);
}
[data-testid="stSidebar"] [role="radiogroup"] label[data-baseweb="radio"] > div:first-child { display: none; }
[data-testid="stSidebar"] .stButton > button {
  background: transparent; color: #E6EAF2; border: 1px solid rgba(255,255,255,0.35); width: 100%;
}
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.12); }
.side-brand { font-family: var(--display); font-weight: 800; font-size: 1.35rem; color: #fff !important;
  letter-spacing: -0.02em; margin: 0.2rem 0 0.1rem; }
.side-brand-bar { display: flex; height: 4px; width: 56px; border-radius: 2px; overflow: hidden; margin-bottom: 1rem; }
.side-brand-bar i { flex: 1; } .side-brand-bar i:first-child { background: var(--for); }
.side-brand-bar i:last-child { background: var(--against); }
.side-hello { font-size: 0.95rem; opacity: 0.85; margin-bottom: 0.6rem; }
.engine { display: flex; align-items: center; gap: 0.5rem; font-size: 0.85rem; padding: 0.55rem 0.7rem;
  border-radius: 8px; background: rgba(255,255,255,0.06); }
.engine .dot { width: 8px; height: 8px; border-radius: 50%; flex: none; }

/* ---------- the motion placard (signature element) ---------- */
.placard { display: grid; grid-template-columns: 72px 1fr 72px; background: #fff; border-radius: 18px;
  overflow: hidden; border: 1px solid var(--line); margin: 0.4rem 0 1.2rem; }
.placard .bench { display: flex; align-items: center; justify-content: center; position: relative; }
.placard .bench.for { background: var(--for); }
.placard .bench.against { background: var(--against); }
.placard .bench span { writing-mode: vertical-rl; transform: rotate(180deg); color: #fff;
  font-family: var(--display); font-weight: 700; font-size: 1.05rem; letter-spacing: 0.04em; }
.placard .bench.against span { transform: none; }
.placard .bench .you { position: absolute; top: 12px; left: 50%; translate: -50% 0; background: var(--gold);
  color: var(--ink); font-size: 0.72rem; font-weight: 700; padding: 2px 8px; border-radius: 999px;
  writing-mode: horizontal-tb; }
.placard .bench.dim { filter: saturate(0.5) brightness(1.1); }
.placard .body { padding: 1.6rem 1.8rem; }
.placard .house { font-family: var(--body); color: var(--muted); font-size: 1rem; margin-bottom: 0.35rem; }
.placard .motion { font-family: var(--display); font-weight: 700; color: var(--ink); line-height: 1.12;
  font-size: clamp(1.35rem, 2.6vw, 1.9rem); letter-spacing: -0.02em; }
.placard.hero { margin-top: 0.2rem; }
.placard.hero .body { padding: 2.6rem 2.4rem; }
.placard.hero .motion { font-size: clamp(2rem, 5vw, 3.4rem); font-weight: 800; }
.placard.hero .bench { width: 100%; animation: bench-in .7s cubic-bezier(.2,.8,.2,1) both; }
.placard.hero .bench.against { animation-delay: .12s; }
@keyframes bench-in { from { transform: scaleY(0); } to { transform: scaleY(1); } }
.placard .meta { margin-top: 0.9rem; color: var(--muted); font-size: 0.95rem; }

/* ---------- landing ---------- */
.brandline { display: flex; align-items: baseline; gap: 0.6rem; margin-bottom: 0.4rem; }
.brandline b { font-family: var(--display); font-size: 1.25rem; font-weight: 800; color: var(--ink); }
.lede { font-size: 1.12rem; line-height: 1.6; color: var(--ink-soft); max-width: 42rem; margin: 0.2rem 0 1.4rem; }
.steps { list-style: none; padding: 0; margin: 0.4rem 0 0; counter-reset: step; max-width: 34rem; }
.steps-title { font-family: var(--display); font-weight: 700; font-size: 1.15rem; color: var(--ink); margin: 0.3rem 0 0.2rem; }
.steps li { counter-increment: step; display: grid; grid-template-columns: 2.2rem 1fr; gap: 0.2rem 0.7rem;
  padding: 0.85rem 0; border-top: 1px solid var(--line); }
.steps li::before { content: counter(step); grid-row: span 2; width: 2rem; height: 2rem; border-radius: 50%;
  display: grid; place-items: center; background: var(--ink); color: #fff; font-weight: 700; font-family: var(--display); }
.steps b { font-family: var(--display); font-size: 1.05rem; color: var(--ink); }
.steps span { color: var(--muted); line-height: 1.5; }

/* ---------- page heads ---------- */
.page-title { font-family: var(--display); font-weight: 800; font-size: clamp(1.8rem, 4vw, 2.5rem);
  color: var(--ink); letter-spacing: -0.025em; margin: 0 0 0.3rem; line-height: 1.1; }
.page-sub { color: var(--muted); font-size: 1.05rem; margin: 0 0 1.4rem; max-width: 40rem; }

/* ---------- scoreboard strip ---------- */
.scoreboard { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); background: #fff;
  border: 1px solid var(--line); border-radius: 16px; margin: 0.4rem 0 1.4rem; }
.scoreboard > div { padding: 1rem 1.2rem; border-left: 1px solid var(--line); }
.scoreboard > div:first-child { border-left: none; }
.scoreboard .num { font-family: var(--display); font-weight: 800; font-size: 1.9rem; color: var(--ink); line-height: 1.1; }
.scoreboard .lbl { color: var(--muted); font-size: 0.9rem; }

/* ---------- round tracker ---------- */
.rounds { display: flex; gap: 6px; margin: 0 0 1.2rem; }
.rounds .r { flex: 1; min-width: 0; }
.rounds .r i { display: block; height: 6px; border-radius: 3px; background: var(--line); margin-bottom: 6px; }
.rounds .r.done i { background: var(--ink); }
.rounds .r.now i { background: var(--gold); }
.rounds .r span { font-size: 0.8rem; color: var(--muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block; }
.rounds .r.now span { color: var(--ink); font-weight: 700; }

/* ---------- chat ---------- */
[data-testid="stChatMessage"] { background: #fff; border: 1px solid var(--line); border-radius: 16px;
  padding: 1rem 1.1rem; margin-bottom: 0.8rem; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) { border-left: 5px solid var(--you, var(--for)); }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) { border-left: 5px solid var(--them, var(--against)); }
.speaker { font-family: var(--display); font-weight: 700; font-size: 0.92rem; margin-bottom: 0.2rem; }
.flagged { display: inline-block; margin-top: 0.4rem; font-size: 0.82rem; color: var(--muted);
  background: var(--paper); border-radius: 999px; padding: 2px 10px; }
.coach { border-radius: 12px; padding: 0.8rem 1rem; margin: 0 0 0.8rem; line-height: 1.5;
  background: #fff; border: 1px dashed var(--line); color: var(--ink-soft); }
.coach b { font-family: var(--display); color: var(--ink); }
.coach.hint { background: var(--gold-tint); border: 1px solid #EED9A6; }
.coach.warning { background: var(--against-tint); border: 1px solid #EBC3CB; }
[data-testid="stChatInput"] { border-radius: 14px; }

/* ---------- judge's scoresheet ---------- */
.sheet { display: grid; grid-template-columns: 240px 1fr; background: #fff; border: 1px solid var(--line);
  border-radius: 18px; overflow: hidden; margin: 0.4rem 0 1.4rem; }
.verdict { background: var(--ink); color: #fff; padding: 1.8rem 1.4rem; display: flex; flex-direction: column;
  justify-content: center; }
.verdict .big { font-family: var(--display); font-weight: 800; font-size: 4.2rem; line-height: 1; color: var(--gold); }
.verdict .big small { font-size: 1.4rem; color: rgba(255,255,255,0.6); font-weight: 700; }
.verdict .word { font-family: var(--display); font-weight: 700; font-size: 1.4rem; margin-top: 0.5rem; }
.verdict .judge { font-size: 0.85rem; color: rgba(255,255,255,0.65); margin-top: 0.8rem; }
.criteria { padding: 1.2rem 1.6rem; }
.crit { padding: 0.7rem 0; border-top: 1px solid var(--line); }
.crit:first-child { border-top: none; }
.crit .head { display: flex; justify-content: space-between; align-items: baseline; }
.crit .name { font-family: var(--display); font-weight: 700; color: var(--ink); }
.crit .val { font-family: var(--display); font-weight: 800; color: var(--ink); }
.crit .bar { height: 8px; border-radius: 4px; background: var(--paper); margin: 0.4rem 0 0.35rem; overflow: hidden; }
.crit .bar i { display: block; height: 100%; border-radius: 4px; background: var(--ink); }
.crit.best .bar i { background: var(--gold); }
.crit .note { color: var(--muted); font-size: 0.88rem; }
.notes { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.6rem; margin-bottom: 1.4rem; }
.notes h4 { font-size: 1.1rem; margin: 0 0 0.5rem; padding-bottom: 0.4rem; border-bottom: 3px solid var(--ink); }
.notes ul { margin: 0; padding-left: 1.1rem; } .notes li { margin-bottom: 0.45rem; line-height: 1.5; color: var(--ink-soft); }
.notes .good h4 { border-color: var(--for); } .notes .bad h4 { border-color: var(--against); }
.notes .next h4 { border-color: var(--gold); }

/* ---------- account ---------- */
.account { background: #fff; border: 1px solid var(--line); border-radius: 16px; max-width: 560px; }
.account > div { display: grid; grid-template-columns: 150px 1fr; padding: 0.9rem 1.2rem; border-top: 1px solid var(--line); }
.account > div:first-child { border-top: none; }
.account dt { color: var(--muted); } .account dd { margin: 0; font-weight: 700; color: var(--ink); word-break: break-word; }

/* ---------- empty states ---------- */
.empty { background: #fff; border: 1px dashed var(--line); border-radius: 16px; padding: 2rem 1.6rem; text-align: center; }
.empty b { font-family: var(--display); font-size: 1.2rem; color: var(--ink); display: block; margin-bottom: 0.3rem; }
.empty span { color: var(--muted); }

/* ---------- phones ---------- */
@media (max-width: 640px) {
  .block-container { padding-top: 1.2rem; }
  .placard { grid-template-columns: 34px 1fr 34px; border-radius: 14px; }
  .placard .bench span { font-size: 0.8rem; }
  .placard .bench .you { top: 8px; font-size: 0.6rem; padding: 1px 5px; }
  .placard .body, .placard.hero .body { padding: 1.3rem 1.1rem; }
  .sheet { grid-template-columns: 1fr; }
  .verdict { flex-direction: row; align-items: baseline; flex-wrap: wrap; gap: 0 1rem; padding: 1.2rem; }
  .verdict .big { font-size: 3rem; }
  .verdict .judge { width: 100%; margin-top: 0.3rem; }
  .criteria { padding: 0.6rem 1.1rem; }
  .notes { grid-template-columns: 1fr; gap: 1rem; }
  .rounds .r span { font-size: 0.7rem; }
  .account > div { grid-template-columns: 1fr; gap: 0.15rem; }
}
@media (prefers-reduced-motion: reduce) { .placard.hero .bench { animation: none; } }
</style>
"""


def motion_phrase(motion: str):
    """Split a motion into ('This House believes that', 'rest of motion')."""
    m = (motion or "").strip().rstrip(".")
    if m.lower().startswith("this house"):
        return None, m
    if len(m) > 1 and not m[1].isupper():          # keep acronyms like "AI should..."
        m = m[0].lower() + m[1:]
    return "This House believes that", m


def placard(motion: str, user_side: str = None, hero: bool = False, meta: str = ""):
    """The split FOR / AGAINST motion card."""
    house, text = motion_phrase(motion)

    def bench(side):
        label = "For" if side == "for" else "Against"
        you = '<b class="you">You</b>' if user_side == side else ""
        dim = ""
        return f'<div class="bench {side}{dim}">{you}<span>{label}</span></div>'

    house_html = f'<div class="house">{house}</div>' if house else ""
    meta_html = f'<div class="meta">{escape(meta)}</div>' if meta else ""
    return (f'<div class="placard{" hero" if hero else ""}">{bench("for")}'
            f'<div class="body">{house_html}<div class="motion">{escape(text)}</div>{meta_html}</div>'
            f'{bench("against")}</div>')


def side_vars(user_side: str):
    """CSS variables so chat bubbles take each speaker's bench colour."""
    them = "against" if user_side == "for" else "for"
    return (f"<style>:root {{ --you: {SIDE_COLORS[user_side]}; --them: {SIDE_COLORS[them]}; }}"
            f".speaker.you {{ color: {SIDE_COLORS[user_side]}; }} .speaker.them {{ color: {SIDE_COLORS[them]}; }}</style>")


def round_tracker(total: int, played: int, active: bool):
    names = ["Opening"] + [f"Rebuttal {i}" for i in range(1, total - 1)] + ["Closing"]
    cells = []
    for i, name in enumerate(names):
        cls = "done" if i < played else ("now" if active and i == played else "")
        cells.append(f'<div class="r {cls}"><i></i><span>{name}</span></div>')
    return f'<div class="rounds" aria-label="Round {min(played + 1, total)} of {total}">{"".join(cells)}</div>'


def scoreboard(items):
    """items: list of (number, label)."""
    cells = "".join(f'<div><div class="num">{escape(str(n))}</div><div class="lbl">{escape(l)}</div></div>'
                    for n, l in items)
    return f'<div class="scoreboard">{cells}</div>'


def verdict_word(overall: float):
    if overall >= 8:
        return "Excellent"
    if overall >= 6.5:
        return "Good"
    if overall >= 5:
        return "Developing"
    return "Needs practice"


def scoresheet(scores: dict, overall: float, labels: dict, explanations: dict = None, judge: str = ""):
    best = max(scores, key=scores.get) if scores else None
    rows = []
    for key, val in scores.items():
        note = (explanations or {}).get(key, "")
        rows.append(
            f'<div class="crit{" best" if key == best else ""}"><div class="head">'
            f'<span class="name">{escape(labels.get(key, key))}</span><span class="val">{val}</span></div>'
            f'<div class="bar"><i style="width:{max(0, min(100, val * 10))}%"></i></div>'
            f'{f"<div class=note>{escape(note)}</div>" if note else ""}</div>')
    judge_html = f'<div class="judge">Judged by {escape(judge)}</div>' if judge else ""
    return (f'<div class="sheet"><div class="verdict"><div class="big">{overall}<small> / 10</small></div>'
            f'<div class="word">{verdict_word(overall)}</div>{judge_html}</div>'
            f'<div class="criteria">{"".join(rows)}</div></div>')


def notes(strengths, weaknesses, recommendations):
    def col(cls, title, items):
        li = "".join(f"<li>{escape(x)}</li>" for x in items or [])
        return f'<div class="{cls}"><h4>{title}</h4><ul>{li}</ul></div>'
    return (f'<div class="notes">{col("good", "What worked", strengths)}'
            f'{col("bad", "What held you back", weaknesses)}{col("next", "Try next time", recommendations)}</div>')


def coach_note(kind: str, text: str):
    title = {"hint": "Hint", "feedback": "Coach", "warning": "Heads up"}.get(kind, "Note")
    return f'<div class="coach {escape(kind)}"><b>{title}.</b> {escape(text)}</div>'


def empty(title: str, text: str):
    return f'<div class="empty"><b>{escape(title)}</b><span>{escape(text)}</span></div>'


def page_head(title: str, sub: str = ""):
    sub_html = f'<p class="page-sub">{escape(sub)}</p>' if sub else ""
    return f'<h1 class="page-title">{escape(title)}</h1>{sub_html}'
