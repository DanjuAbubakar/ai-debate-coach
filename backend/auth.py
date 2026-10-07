"""
User accounts: registration, login and login tokens.

Passwords are NEVER stored as plain text. Each password is mixed with a random
"salt" and scrambled 200,000 times with PBKDF2-SHA256 (Python's built-in hashlib),
so even someone who opens the database file can't read anyone's password.

No extra packages needed - everything here is in Python's standard library.
"""
import hashlib
import hmac
import re
import secrets

ITERATIONS = 200_000
TOKEN_DAYS = 7

USERNAME_RE = re.compile(r"^[A-Za-z0-9_.]{3,30}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AuthError(ValueError):
    """Bad registration/login details (HTTP 400/401)."""


def hash_password(password: str, salt: str = None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), ITERATIONS).hex()
    return f"pbkdf2_sha256${ITERATIONS}${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iterations, salt, digest = stored.split("$")
        check = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(iterations)).hex()
        return hmac.compare_digest(check, digest)
    except (ValueError, AttributeError):
        return False


def new_token() -> str:
    return secrets.token_urlsafe(32)


def validate_registration(full_name: str, username: str, email: str, password: str):
    full_name = (full_name or "").strip()
    username = (username or "").strip()
    email = (email or "").strip().lower()
    if len(full_name) < 2:
        raise AuthError("Please enter your full name.")
    if len(full_name) > 80:
        raise AuthError("Full name is too long.")
    if not USERNAME_RE.match(username):
        raise AuthError("Username must be 3-30 characters: letters, numbers, dots or underscores only (no spaces).")
    if not EMAIL_RE.match(email):
        raise AuthError("Please enter a valid email address.")
    if len(password or "") < 6:
        raise AuthError("Password must be at least 6 characters.")
    if password.lower() in {"password", "123456", "12345678", "qwerty", username.lower()}:
        raise AuthError("That password is too easy to guess. Please choose another one.")
    return full_name, username, email
