"""
Storage (Week 9) - works with TWO kinds of database, same code:

  * SQLite   - a single file on your laptop (default, nothing to set up)
  * Postgres - an online database for the deployed app (e.g. Neon, free).
               Used automatically when the DATABASE_URL environment variable is set.

Why two? Free hosting (Render) wipes its disk whenever the server restarts,
so a SQLite file there would lose every account. An online Postgres keeps them.

Tables:
  users       - registered accounts (full name, username, email, hashed password)
  auth_tokens - login tokens; each login creates one, logout deletes it
  debates     - one row per COMPLETED debate, with scores and the full transcript

Live debates in progress stay in memory only (engine.py); they are saved here
once the user ends the debate and receives a score.
"""
import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

import auth

DEFAULT_DB = Path(__file__).resolve().parent / "data" / "debate_coach.db"
DB_PATH = Path(os.getenv("DEBATE_DB_PATH", str(DEFAULT_DB)))
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    created_at    TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS debates (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT NOT NULL UNIQUE,
    user_id         INTEGER NOT NULL REFERENCES users(id),
    motion          TEXT NOT NULL,
    category        TEXT,
    user_side       TEXT NOT NULL,
    difficulty      TEXT NOT NULL,
    rounds_played   INTEGER NOT NULL,
    hints_used      INTEGER NOT NULL DEFAULT 0,
    overall_score   REAL NOT NULL,
    scores_json     TEXT NOT NULL,
    feedback_json   TEXT NOT NULL,
    summary         TEXT,
    transcript_json TEXT NOT NULL,
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_debates_user ON debates(user_id, created_at);
CREATE TABLE IF NOT EXISTS auth_tokens (
    token       TEXT PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at  TEXT NOT NULL,
    expires_at  TEXT NOT NULL
);
"""

POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    username      TEXT NOT NULL UNIQUE,
    created_at    TEXT NOT NULL,
    full_name     TEXT,
    email         TEXT,
    password_hash TEXT,
    last_login    TEXT
);
CREATE TABLE IF NOT EXISTS debates (
    id              SERIAL PRIMARY KEY,
    session_id      TEXT NOT NULL UNIQUE,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    motion          TEXT NOT NULL,
    category        TEXT,
    user_side       TEXT NOT NULL,
    difficulty      TEXT NOT NULL,
    rounds_played   INTEGER NOT NULL,
    hints_used      INTEGER NOT NULL DEFAULT 0,
    overall_score   REAL NOT NULL,
    scores_json     TEXT NOT NULL,
    feedback_json   TEXT NOT NULL,
    summary         TEXT,
    transcript_json TEXT NOT NULL,
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_debates_user ON debates(user_id, created_at);
CREATE TABLE IF NOT EXISTS auth_tokens (
    token       TEXT PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at  TEXT NOT NULL,
    expires_at  TEXT NOT NULL
);
"""

# Columns added when accounts were introduced. Older SQLite files get them automatically.
USER_COLUMNS = {"full_name": "TEXT", "email": "TEXT", "password_hash": "TEXT", "last_login": "TEXT"}
PUBLIC_USER_FIELDS = ("id", "username", "full_name", "email", "created_at", "last_login")


class _Connection:
    """
    One small wrapper so the rest of the code doesn't care which database it is.
    Write SQL with ? placeholders; they're converted for Postgres automatically.
    """

    def __init__(self, db_path=None, url=None):
        self.url = url
        self.kind = "postgres" if url else "sqlite"
        self.db_path = Path(db_path or DB_PATH)
        self.lock = threading.RLock()
        self._connect()

    def _connect(self):
        if self.kind == "postgres":
            import psycopg                      # only needed on the server (backend/requirements.txt)
            from psycopg.rows import dict_row
            self.raw = psycopg.connect(self.url, row_factory=dict_row, autocommit=True)
        else:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self.raw = sqlite3.connect(self.db_path, check_same_thread=False, isolation_level=None)
            self.raw.row_factory = sqlite3.Row
            self.raw.execute("PRAGMA foreign_keys = ON")

    def _sql(self, sql):
        return sql.replace("?", "%s") if self.kind == "postgres" else sql

    def _run(self, sql, params=()):
        """Run one statement. Online databases drop idle connections, so reconnect once if needed."""
        for attempt in range(2):
            try:
                if self.kind == "postgres":
                    return self.raw.execute(self._sql(sql), params or None)
                return self.raw.execute(sql, params)
            except Exception as e:
                if self.kind == "postgres" and attempt == 0 and type(e).__name__ in (
                        "OperationalError", "InterfaceError"):
                    self._connect()
                    continue
                raise

    def execute(self, sql, params=()):
        with self.lock:
            return self._run(sql, params)

    def fetchone(self, sql, params=()):
        with self.lock:
            row = self._run(sql, params).fetchone()
        return dict(row) if row else None

    def fetchall(self, sql, params=()):
        with self.lock:
            rows = self._run(sql, params).fetchall()
        return [dict(r) for r in rows]

    def insert(self, sql, params=()):
        """INSERT and return the new row's id."""
        with self.lock:
            if self.kind == "postgres":
                return self._run(sql + " RETURNING id", params).fetchone()["id"]
            return self._run(sql, params).lastrowid

    @contextmanager
    def transaction(self):
        """All-or-nothing: if anything fails inside, nothing is saved (Week 10 fix)."""
        with self.lock:
            if self.kind == "postgres":
                with self.raw.transaction():
                    yield self
            else:
                self.raw.execute("BEGIN")
                try:
                    yield self
                    self.raw.execute("COMMIT")
                except Exception:
                    self.raw.execute("ROLLBACK")
                    raise

    def script(self, sql_script):
        with self.lock:
            for stmt in [s.strip() for s in sql_script.split(";") if s.strip()]:
                self._run(stmt)


class Database:
    def __init__(self, db_path=None, url=None):
        url = url if url is not None else (None if db_path else DATABASE_URL or None)
        self.db = _Connection(db_path=db_path, url=url)
        self.kind = self.db.kind
        if self.kind == "postgres":
            self.db.script(POSTGRES_SCHEMA)
        else:
            self.db.script(SQLITE_SCHEMA)
            existing = {r["name"] for r in self.db.fetchall("PRAGMA table_info(users)")}
            for col, kind in USER_COLUMNS.items():
                if col not in existing:
                    self.db.execute(f"ALTER TABLE users ADD COLUMN {col} {kind}")
        self.db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users (lower(email)) "
                        "WHERE email IS NOT NULL")

    @staticmethod
    def _now():
        return datetime.now().isoformat(timespec="seconds")

    # ---- accounts ----
    @staticmethod
    def public(user: dict) -> dict:
        """User details that are safe to send to the browser (never the password hash)."""
        return {k: user.get(k) for k in PUBLIC_USER_FIELDS}

    def register(self, full_name, username, email, password) -> dict:
        full_name, username, email = auth.validate_registration(full_name, username, email, password)
        existing = self.find_user(username)
        if existing and existing.get("password_hash"):
            raise auth.AuthError("That username is already taken. Try another, or log in instead.")
        taken = self.db.fetchone("SELECT id FROM users WHERE lower(email)=lower(?)", (email,))
        if taken and (not existing or taken["id"] != existing["id"]):
            raise auth.AuthError("An account with that email already exists. Log in instead.")
        pw = auth.hash_password(password)
        with self.db.transaction() as t:
            if existing:   # an old name-only profile from before accounts existed: claim it and keep its history
                t.execute("UPDATE users SET full_name=?, email=?, password_hash=? WHERE id=?",
                          (full_name, email, pw, existing["id"]))
                user_id = existing["id"]
            else:
                user_id = t.insert("INSERT INTO users (username, full_name, email, password_hash, created_at) "
                                   "VALUES (?,?,?,?,?)", (username, full_name, email, pw, self._now()))
        return self.user_by_id(user_id)

    def login(self, login: str, password: str) -> dict:
        """Log in with username OR email."""
        login = (login or "").strip()
        row = self.db.fetchone("SELECT * FROM users WHERE lower(username)=lower(?) OR lower(email)=lower(?)",
                               (login, login))
        if not row or not row["password_hash"] or not auth.verify_password(password or "", row["password_hash"]):
            raise auth.AuthError("Wrong username/email or password.")
        self.db.execute("UPDATE users SET last_login=? WHERE id=?", (self._now(), row["id"]))
        return self.user_by_id(row["id"])

    def user_by_id(self, user_id):
        return self.db.fetchone("SELECT * FROM users WHERE id=?", (user_id,))

    def create_token(self, user_id) -> str:
        token = auth.new_token()
        now = datetime.now()
        self.db.execute("DELETE FROM auth_tokens WHERE expires_at < ?", (now.isoformat(),))
        self.db.execute("INSERT INTO auth_tokens (token, user_id, created_at, expires_at) VALUES (?,?,?,?)",
                        (token, user_id, now.isoformat(timespec="seconds"),
                         (now + timedelta(days=auth.TOKEN_DAYS)).isoformat(timespec="seconds")))
        return token

    def user_for_token(self, token):
        if not token:
            return None
        return self.db.fetchone("SELECT u.* FROM auth_tokens t JOIN users u ON u.id=t.user_id "
                                "WHERE t.token=? AND t.expires_at > ?", (token, datetime.now().isoformat()))

    def delete_token(self, token):
        self.db.execute("DELETE FROM auth_tokens WHERE token=?", (token,))

    # ---- users ----
    def get_or_create_user(self, username: str) -> dict:
        username = username.strip()
        existing = self.find_user(username)
        if existing:
            return existing
        user_id = self.db.insert("INSERT INTO users (username, created_at) VALUES (?, ?)", (username, self._now()))
        return self.user_by_id(user_id)

    def find_user(self, username: str):
        return self.db.fetchone("SELECT * FROM users WHERE lower(username)=lower(?)", (username.strip(),))

    # ---- debates ----
    def save_debate(self, user_id, session, scorecard, summary) -> int:
        feedback = {"strengths": scorecard.strengths, "weaknesses": scorecard.weaknesses,
                    "recommendations": scorecard.recommendations, "evaluator": scorecard.evaluator}
        with self.db.transaction() as t:
            t.execute("DELETE FROM debates WHERE session_id=?", (session.id,))
            return t.insert(
                """INSERT INTO debates
                   (session_id, user_id, motion, category, user_side, difficulty, rounds_played, hints_used,
                    overall_score, scores_json, feedback_json, summary, transcript_json, created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (session.id, user_id, session.motion, session.category, session.user_side, session.difficulty,
                 session.rounds_played(), session.hints_used, scorecard.overall_score,
                 json.dumps(scorecard.scores), json.dumps(feedback), summary,
                 json.dumps(session.messages), self._now()))

    @staticmethod
    def _row_to_dict(row, full=False):
        d = dict(row)
        d["scores"] = json.loads(d.pop("scores_json"))
        d["feedback"] = json.loads(d.pop("feedback_json"))
        transcript = json.loads(d.pop("transcript_json"))
        if full:
            d["transcript"] = transcript
        return d

    def list_debates(self, user_id):
        rows = self.db.fetchall("SELECT * FROM debates WHERE user_id=? ORDER BY created_at DESC, id DESC", (user_id,))
        return [self._row_to_dict(r) for r in rows]

    def get_debate(self, debate_id: int):
        row = self.db.fetchone("SELECT * FROM debates WHERE id=?", (debate_id,))
        return self._row_to_dict(row, full=True) if row else None

    def delete_debate(self, debate_id: int):
        return self.db.execute("DELETE FROM debates WHERE id=?", (debate_id,)).rowcount > 0

    def stats(self, user_id) -> dict:
        """Week 9 Thursday: average, strongest and weakest criterion."""
        debates = list(reversed(self.list_debates(user_id)))  # oldest first
        n = len(debates)
        result = {"total_debates": n, "average_score": None, "best_score": None, "strongest": None,
                  "weakest": None, "criteria_averages": {}, "recent_average": None, "earlier_average": None,
                  "timeline": []}
        if n == 0:
            return result
        overall = [d["overall_score"] for d in debates]
        result["average_score"] = round(sum(overall) / n, 1)
        result["best_score"] = max(overall)
        crit = {}
        for d in debates:
            for k, v in d["scores"].items():
                crit.setdefault(k, []).append(v)
        avgs = {k: round(sum(v) / len(v), 1) for k, v in crit.items()}
        result["criteria_averages"] = avgs
        result["strongest"] = max(avgs, key=avgs.get)
        result["weakest"] = min(avgs, key=avgs.get)
        if n >= 2:
            half = max(1, n // 2)
            earlier, recent = overall[:half], overall[half:]
            result["earlier_average"] = round(sum(earlier) / len(earlier), 1)
            result["recent_average"] = round(sum(recent) / len(recent), 1)
        result["timeline"] = [{"debate": i + 1, "date": d["created_at"][:10], "score": d["overall_score"],
                               "difficulty": d["difficulty"]} for i, d in enumerate(debates)]
        return result
