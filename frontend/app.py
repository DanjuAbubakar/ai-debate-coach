"""
AI Debate Coach - Streamlit frontend (Week 5, 6, 9).

Logged-out visitors see the landing page (log in / create account).
Logged-in users get the full app and only ever see their own history.
The look and feel lives in ui.py.

Run from the frontend folder (with the backend already running):
    streamlit run app.py
"""
import os
import re
from html import escape

import pandas as pd
import requests
import streamlit as st

import ui


def _backend_url():
    """Locally: http://localhost:8000. On Streamlit Cloud: the BACKEND_URL secret."""
    try:
        if "BACKEND_URL" in st.secrets:
            return str(st.secrets["BACKEND_URL"])
    except Exception:          # no secrets file when running locally
        pass
    return os.getenv("BACKEND_URL", "http://localhost:8000")


API = _backend_url().rstrip("/")
PAGES = ["Home", "New debate", "Debate room", "Results", "Progress", "Account"]
LABELS = {"logic": "Logic", "relevance": "Relevance", "evidence": "Evidence", "clarity": "Clarity",
          "rebuttal_quality": "Rebuttal quality", "persuasiveness": "Persuasiveness"}
JUDGES = {"online": "the online AI judge", "ollama": "the local AI judge", "llm": "the AI judge",
          "offline": "the offline judge"}

st.set_page_config(page_title="AI Debate Coach", page_icon="🎤", layout="wide")
st.markdown(ui.CSS, unsafe_allow_html=True)

ss = st.session_state
ss.setdefault("nav", PAGES[0])
ss.setdefault("session", None)
ss.setdefault("token", None)
ss.setdefault("user", None)
ss.setdefault("flash", None)
if "_goto" in ss:                 # apply a page change requested on the previous run
    ss.nav = ss.pop("_goto")


def html(markup):
    st.markdown(markup, unsafe_allow_html=True)


# ------------------------------------------------------------------ API helpers
def log_out_locally(message=None):
    for k in ("token", "user", "session"):
        ss[k] = None
    ss.flash = message
    ss._goto = PAGES[0]


def api(method, path, **kwargs):
    """Call the backend. Returns (data, error_message). Sends the login token when we have one."""
    headers = kwargs.pop("headers", {})
    if ss.token:
        headers["Authorization"] = f"Bearer {ss.token}"
    try:
        r = requests.request(method, f"{API}{path}", timeout=180, headers=headers, **kwargs)
    except requests.exceptions.ConnectionError:
        return None, "Can't reach the server right now. If you're running it locally, start run_backend.bat first."
    except requests.exceptions.Timeout:
        return None, "The AI took too long to respond. Send your argument again."
    if r.status_code == 401 and ss.token:          # token expired or revoked
        log_out_locally("Your login has expired. Log in again to continue.")
        st.rerun()
    if r.status_code >= 400:
        try:
            detail = r.json().get("detail")
            if isinstance(detail, list):  # FastAPI validation error
                detail = "; ".join(d.get("msg", "") for d in detail)
        except ValueError:
            detail = r.text
        return None, detail or f"Error {r.status_code}"
    return r.json(), None


def go(page):
    """Ask for a page change. It is applied at the top of the next run, before the menu is drawn."""
    ss._goto = page


# ------------------------------------------------------------------ landing page (logged out)
def landing_page():
    html("""<style>[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
            [data-testid="collapsedControl"], [data-testid="stExpandSidebarButton"] {display: none;}</style>""")
    if ss.flash:
        st.warning(ss.flash)
        ss.flash = None

    html('<div class="brandline"><b>🎤 AI Debate Coach</b></div>')
    html(ui.placard("Every argument deserves an opponent", hero=True))

    html('<p class="lede">Choose a motion and a side. The AI takes the other bench, challenges every claim '
         'you make, and then scores you the way a judge would. Your debates are saved so you can see '
         'yourself improve.</p>')

    # Form first, so on a phone it comes straight after the intro instead of below the steps.
    left, right = st.columns([1, 1.1], gap="large")
    with right:
        html('<div class="steps-title">How it works</div>'
             '<ol class="steps">'
             '<li><b>Choose a motion</b><span>Pick one of ours or write your own.</span></li>'
             '<li><b>Take a side</b><span>For or against. Your opponent argues the opposite.</span></li>'
             '<li><b>Debate</b><span>Opening, rebuttals and closing, with a hint whenever you\'re stuck.</span></li>'
             '<li><b>Get your scoresheet</b><span>Logic, relevance, evidence, clarity, rebuttal and '
             'persuasiveness, each out of 10.</span></li></ol>')

    with left:
        login_tab, register_tab = st.tabs(["Log in", "Create account"])
        with login_tab:
            with st.form("login_form"):
                login = st.text_input("Username or email")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Log in", type="primary")
            if submitted:
                if not login or not password:
                    st.error("Enter your username or email, and your password.")
                else:
                    with st.spinner("Logging you in. The first visit of the day can take up to a minute."):
                        data, e = api("POST", "/auth/login", json={"login": login, "password": password})
                    if e:
                        st.error(e)
                    else:
                        ss.token, ss.user = data["token"], data["user"]
                        go(PAGES[0])
                        st.rerun()
        with register_tab:
            with st.form("register_form"):
                full_name = st.text_input("Full name", placeholder="e.g. Danjuma Abubakar")
                username = st.text_input("Username", placeholder="Letters, numbers, dots or underscores")
                email = st.text_input("Email")
                pw1 = st.text_input("Password", type="password", help="At least 6 characters")
                pw2 = st.text_input("Confirm password", type="password")
                created = st.form_submit_button("Create account", type="primary")
            if created:
                if pw1 != pw2:
                    st.error("The two passwords don't match. Type them again.")
                else:
                    with st.spinner("Creating your account. The first visit of the day can take up to a minute."):
                        data, e = api("POST", "/auth/register", json={"full_name": full_name, "username": username,
                                                                       "email": email, "password": pw1})
                    if e:
                        st.error(e)
                    else:
                        ss.token, ss.user = data["token"], data["user"]
                        go(PAGES[0])
                        st.rerun()


if not ss.token:
    landing_page()
    st.stop()


# ------------------------------------------------------------------ sidebar (logged in)
first_name = (ss.user.get("full_name") or ss.user["username"]).split()[0]

with st.sidebar:
    html('<div class="side-brand">AI Debate Coach</div><div class="side-brand-bar"><i></i><i></i></div>'
         f'<div class="side-hello">Signed in as {escape(first_name)}</div>')
    st.radio("Navigate", PAGES, key="nav", label_visibility="collapsed")
    st.divider()
    health, err = api("GET", "/health")
    if err:
        engine, dot = "Server offline", "#B3263E"
    else:
        engine, dot = {"online": ("Online AI", "#3DDC97"), "ollama": (f"Local AI ({health['ollama_model']})", "#3DDC97")
                       }.get(health["ai_mode"], ("Offline brain", "#E3A72F"))
    html(f'<div class="engine"><span class="dot" style="background:{dot}"></span>Opponent: {escape(engine)}</div>')
    if ss.session and ss.session["status"] == "active":
        s = ss.session
        st.caption(f"Debate in progress: round {s['current_round']} of {s['total_rounds']}")
    st.write("")
    if st.button("Log out"):
        api("POST", "/auth/logout")
        log_out_locally()
        st.rerun()


# ------------------------------------------------------------------ pages
def page_home():
    html(ui.page_head(f"Welcome back, {first_name}", "Ready for another round? Pick a motion and take a side."))
    stats, _ = api("GET", "/me/stats")
    if stats and stats["total_debates"]:
        html(ui.scoreboard([
            (stats["total_debates"], "Debates finished"),
            (stats["average_score"], "Average score"),
            (stats["best_score"], "Best score"),
            (LABELS.get(stats["strongest"], "-"), "Strongest skill"),
        ]))
    else:
        html(ui.empty("No debates yet", "Your scores will show up here after your first debate."))
        st.write("")
    c1, c2, _ = st.columns([1, 1, 2])
    c1.button("Start a debate", type="primary", on_click=go, args=(PAGES[1],))
    c2.button("See my progress", on_click=go, args=(PAGES[4],))
    if ss.session and ss.session["status"] == "active":
        st.write("")
        st.info(f"You have a debate in progress on \"{ss.session['motion']}\".")
        st.button("Continue debate", on_click=go, args=(PAGES[2],))


def page_setup():
    html(ui.page_head("New debate", "Choose the motion, your side and how tough your opponent should be."))
    topics, terr = api("GET", "/topics")
    if terr:
        st.error(terr)
        return

    use_custom = st.toggle("Write my own motion")
    if use_custom:
        motion = st.text_input("Motion", placeholder="e.g. Students should wear uniforms in university")
        category = "Custom"
    else:
        c1, c2 = st.columns([1, 2])
        category = c1.selectbox("Category", list(topics))
        motion = c2.selectbox("Motion", topics[category])

    c1, c2, c3 = st.columns(3)
    side = c1.radio("Your side", ["For", "Against"], horizontal=True)
    difficulty = c2.select_slider("Opponent", ["Beginner", "Intermediate", "Advanced"], value="Intermediate")
    rounds = c3.slider("Rounds", 3, 6, 4, help="Opening, rebuttals, then closing")

    if motion and motion.strip():
        tip = {"Beginner": "Your opponent uses simple language and makes one point at a time.",
               "Intermediate": "Your opponent asks for examples and points out weak reasoning.",
               "Advanced": "Your opponent challenges your assumptions and demands evidence for every claim."}[difficulty]
        html(ui.placard(motion, side.lower(), meta=f"{rounds} rounds. {tip}"))

    b1, b2 = st.columns([1, 3])
    if b1.button("Start debate", type="primary", disabled=not (motion and motion.strip())):
        with st.spinner("Your opponent is preparing an opening statement..."):
            data, e = api("POST", "/debates/start", json={
                "motion": motion, "side": side.lower(), "difficulty": difficulty.lower(),
                "rounds": rounds, "category": category})
        if e:
            st.error(e)
        else:
            ss.session = data
            go(PAGES[2])
            st.rerun()
    if ss.session and ss.session["status"] == "active":
        b2.caption("Starting a new debate will replace the one in progress.")


def _clean_coach_text(text):
    return re.sub(r"^(Hint:|Coach's note:)\s*", "", text.strip())


def render_message(m, user_side="for"):
    if m["role"] == "user":
        with st.chat_message("user"):
            html(f'<div class="speaker you">You, {"for" if user_side == "for" else "against"} the motion</div>')
            st.markdown(m["content"])
            if m.get("kind") == "flagged":
                html('<span class="flagged">Not counted as an argument</span>')
    elif m["role"] == "assistant":
        with st.chat_message("assistant"):
            other = "against" if user_side == "for" else "for"
            html(f'<div class="speaker them">Opponent, {other} the motion</div>')
            st.markdown(m["content"])
    else:  # coach notes, hints, warnings
        html(ui.coach_note(m.get("kind", "feedback"), _clean_coach_text(m["content"])))


def page_room():
    s = ss.session
    if not s:
        html(ui.page_head("Debate room"))
        html(ui.empty("No debate in progress", "Set one up and your opponent will open the debate."))
        st.write("")
        st.button("Set up a debate", type="primary", on_click=go, args=(PAGES[1],))
        return

    html(ui.side_vars(s["user_side"]))
    html(ui.placard(s["motion"], s["user_side"],
                    meta=f"{s['difficulty'].title()} opponent. Hints used: {s['hints_used']}."))
    active = s["status"] == "active"
    html(ui.round_tracker(s["total_rounds"], s["rounds_played"], active))

    for m in s["display"]:
        render_message(m, s["user_side"])

    c1, c2, _ = st.columns([1, 1.6, 2])
    if c1.button("Get a hint", disabled=not active, help="A nudge in the right direction, not the answer"):
        with st.spinner("Thinking of a hint..."):
            data, e = api("POST", f"/debates/{s['session_id']}/hint")
        if e:
            st.error(e)
        else:
            ss.session = data
            st.rerun()
    end_label = "End debate and get feedback" if s["status"] != "evaluated" else "View scoresheet"
    if c2.button(end_label, type="secondary" if active else "primary", disabled=s["rounds_played"] == 0):
        if s["status"] != "evaluated":
            with st.spinner("The judge is scoring your debate..."):
                data, e = api("POST", f"/debates/{s['session_id']}/end")
            if e:
                st.error(e)
                return
            ss.session = data
        go(PAGES[3])
        st.rerun()

    if active:
        placeholder = {"Opening": "Give your opening argument", "Closing": "Give your closing statement"}.get(
            s["round_name"], "Respond to your opponent")
        text = st.chat_input(placeholder, max_chars=2000)
        if text:
            with st.spinner("Your opponent is thinking..."):
                data, e = api("POST", f"/debates/{s['session_id']}/argue", json={"message": text})
            if e:
                st.error(e)
            else:
                ss.session = data
                st.rerun()
    elif s["status"] == "finished":
        st.success("That's the end of the debate. Get your feedback to see how you scored.")


def render_scorecard(scores, overall, feedback, explanations=None):
    judge = JUDGES.get(feedback.get("evaluator"), "")
    html(ui.scoresheet(scores, overall, LABELS, explanations, judge))
    html(ui.notes(feedback.get("strengths"), feedback.get("weaknesses"), feedback.get("recommendations")))


def page_results():
    s = ss.session
    if not s or not s.get("scorecard"):
        html(ui.page_head("Results"))
        html(ui.empty("No scoresheet yet", "Finish a debate and get feedback to see your scores here."))
        return
    card = s["scorecard"]
    html(ui.page_head("Your scoresheet"))
    html(ui.placard(s["motion"], s["user_side"],
                    meta=f"{s['difficulty'].title()} opponent, {s['rounds_played']} rounds, {s['hints_used']} hints."))
    render_scorecard(card["scores"], card["overall_score"], card, card.get("explanations"))
    if s.get("debate_id"):
        st.caption("Saved to your progress.")
    with st.expander("Read the full debate"):
        html(ui.side_vars(s["user_side"]))
        for m in s["display"]:
            render_message(m, s["user_side"])
    st.button("Start another debate", type="primary", on_click=go, args=(PAGES[1],))


def page_history():
    html(ui.page_head("Your progress", "Every finished debate, and how your skills are changing over time."))
    stats, e = api("GET", "/me/stats")
    if e:
        st.error(e)
        return
    if stats["total_debates"] == 0:
        html(ui.empty("Nothing to show yet", "Finish your first debate and your progress will appear here."))
        st.write("")
        st.button("Start a debate", type="primary", on_click=go, args=(PAGES[1],))
        return

    html(ui.scoreboard([
        (stats["total_debates"], "Debates finished"),
        (stats["average_score"], "Average score"),
        (LABELS.get(stats["strongest"], "-"), "Strongest skill"),
        (LABELS.get(stats["weakest"], "-"), "Work on next"),
    ]))
    html(ui.coach_note("feedback", stats["progress_summary"]))

    g1, g2 = st.columns(2)
    with g1:
        st.markdown("**Score over time**")
        tl = pd.DataFrame(stats["timeline"]).rename(columns={"debate": "Debate", "score": "Score"})
        st.line_chart(tl, x="Debate", y="Score", height=240, color="#16213E")
    with g2:
        st.markdown("**Average by skill**")
        ca = pd.DataFrame({"Skill": [LABELS[k] for k in stats["criteria_averages"]],
                           "Average": list(stats["criteria_averages"].values())})
        st.bar_chart(ca, x="Skill", y="Average", height=240, color="#E3A72F")

    history, e = api("GET", "/me/history")
    if e:
        st.error(e)
        return
    st.markdown("### Past debates")
    df = pd.DataFrame([{"Date": d["created_at"].replace("T", " ")[:16], "Motion": d["motion"],
                        "Side": d["user_side"].title(), "Opponent": d["difficulty"].title(),
                        "Score": d["overall_score"]} for d in history])
    st.dataframe(df, hide_index=True)

    options = {f"{d['motion']} ({d['overall_score']}/10, {d['created_at'][:10]})": d["id"] for d in history}
    choice = st.selectbox("Open a past debate", list(options))
    if choice:
        d, e = api("GET", f"/me/history/{options[choice]}")
        if e:
            st.error(e)
            return
        html(ui.placard(d["motion"], d["user_side"], meta=f"{d['difficulty'].title()} opponent, {d['created_at'][:10]}."))
        render_scorecard(d["scores"], d["overall_score"], d["feedback"])
        with st.expander("Read the full debate"):
            html(ui.side_vars(d["user_side"]))
            for m in d["transcript"]:
                render_message({**m, "kind": "message"}, d["user_side"])


def page_account():
    html(ui.page_head("Your account"))
    me, e = api("GET", "/auth/me")
    if e:
        st.error(e)
        return
    rows = [("Full name", me.get("full_name") or "-"), ("Username", me["username"]),
            ("Email", me.get("email") or "-"), ("Member since", (me.get("created_at") or "")[:10])]
    html('<dl class="account">' + "".join(f"<div><dt>{escape(k)}</dt><dd>{escape(str(v))}</dd></div>"
                                          for k, v in rows) + "</dl>")
    st.caption("Your password is stored as a scrambled hash, so nobody can read it, not even the app owner.")


{PAGES[0]: page_home, PAGES[1]: page_setup, PAGES[2]: page_room,
 PAGES[3]: page_results, PAGES[4]: page_history, PAGES[5]: page_account}[ss.nav]()
