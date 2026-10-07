"""Accounts: registration, login, tokens, and keeping users' history private."""
import sqlite3

import pytest

import auth
from auth import AuthError
from database import Database
from engine import DebateCoach


@pytest.fixture
def db(tmp_path):
    return Database(tmp_path / "auth.db")


def test_password_is_hashed_not_stored(db):
    user = db.register("Danjuma Abubakar", "danjuma", "dan@example.com", "secret123")
    assert user["password_hash"] != "secret123" and user["password_hash"].startswith("pbkdf2_sha256$")
    assert auth.verify_password("secret123", user["password_hash"])
    assert not auth.verify_password("wrong", user["password_hash"])
    assert "password_hash" not in db.public(user)


def test_login_with_username_or_email(db):
    db.register("Ada Obi", "ada_o", "ada@example.com", "debate99")
    assert db.login("ada_o", "debate99")["username"] == "ada_o"
    assert db.login("ADA@example.com", "debate99")["username"] == "ada_o"
    with pytest.raises(AuthError):
        db.login("ada_o", "nope-nope")
    with pytest.raises(AuthError):
        db.login("ghost", "debate99")


@pytest.mark.parametrize("full_name,username,email,password", [
    ("A", "good_name", "a@b.com", "secret123"),              # name too short
    ("Ada Obi", "has space", "a@b.com", "secret123"),        # bad username
    ("Ada Obi", "ada", "not-an-email", "secret123"),         # bad email
    ("Ada Obi", "ada", "a@b.com", "123"),                    # short password
    ("Ada Obi", "ada", "a@b.com", "password"),               # common password
])
def test_registration_validation(db, full_name, username, email, password):
    with pytest.raises(AuthError):
        db.register(full_name, username, email, password)


def test_duplicate_username_and_email(db):
    db.register("Ada Obi", "ada", "ada@example.com", "secret123")
    with pytest.raises(AuthError):
        db.register("Other", "ADA", "other@example.com", "secret123")
    with pytest.raises(AuthError):
        db.register("Other", "other", "ada@example.com", "secret123")


def test_tokens(db):
    user = db.register("Ada Obi", "ada", "ada@example.com", "secret123")
    token = db.create_token(user["id"])
    assert db.user_for_token(token)["id"] == user["id"]
    assert db.user_for_token("made-up-token") is None
    db.delete_token(token)
    assert db.user_for_token(token) is None


def test_expired_token_rejected(db):
    user = db.register("Ada Obi", "ada", "ada@example.com", "secret123")
    token = db.create_token(user["id"])
    db.db.execute("UPDATE auth_tokens SET expires_at='2000-01-01T00:00:00' WHERE token=?", (token,))
    assert db.user_for_token(token) is None


def test_old_database_is_upgraded_and_profile_claimed(tmp_path):
    path = tmp_path / "old.db"
    old = sqlite3.connect(path)
    old.executescript("CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, "
                      "created_at TEXT NOT NULL); INSERT INTO users(username, created_at) VALUES ('danjuma', '2026-10-01');")
    old.commit()
    old.close()
    db = Database(path)                              # adds the new columns automatically
    user = db.register("Danjuma Abubakar", "danjuma", "dan@example.com", "secret123")
    assert user["id"] == 1                           # same profile, so old history is kept
    assert db.login("danjuma", "secret123")["email"] == "dan@example.com"


def test_users_only_see_their_own_history(tmp_path):
    db = Database(tmp_path / "priv.db")
    coach = DebateCoach(db=db, seed=1)
    a = db.register("Ada Obi", "ada", "ada@example.com", "secret123")
    b = db.register("Bayo Ade", "bayo", "bayo@example.com", "secret123")
    s = coach.start("Plastic bags should be banned", "for", total_rounds=3, username="ada")
    coach.argue(s.id, "Plastic bags block drains because they don't break down, for example in Lagos floods.")
    coach.end(s.id)
    assert len(db.list_debates(a["id"])) == 1
    assert db.list_debates(b["id"]) == []
