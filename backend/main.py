"""
AI Debate Coach - FastAPI backend (Week 4).

Run from the backend folder:
    uvicorn main:app --reload --port 8000
Interactive API docs: http://localhost:8000/docs

Accounts: register or log in to get a token, then send it on every request as
    Authorization: Bearer <token>
Each user can only see and use their own debates and history.
"""
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

import llm
from auth import AuthError
from engine import DebateCoach, NotFoundError, StateError
from guardrails import GuardrailError
from topics import all_topics

app = FastAPI(
    title="AI Debate Coach API",
    description="Practise debating against an AI opponent and get structured feedback. No API keys required.",
    version="2.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

coach = DebateCoach()
db = coach.db


# ---------------------------------------------------------------- request models
class RegisterIn(BaseModel):
    full_name: str = Field(max_length=80)
    username: str = Field(max_length=30)
    email: str = Field(max_length=120)
    password: str = Field(max_length=128)


class LoginIn(BaseModel):
    login: str = Field(max_length=120, description="Username or email")
    password: str = Field(max_length=128)


class StartIn(BaseModel):
    motion: str = Field(min_length=1, max_length=300)
    side: str = Field(description="'for' or 'against'")
    difficulty: str = "intermediate"
    rounds: int = 4
    category: Optional[str] = None


class ArgueIn(BaseModel):
    message: str


# ---------------------------------------------------------------- error handling (Week 4 Thursday)
@app.exception_handler(GuardrailError)
async def guardrail_handler(_: Request, exc: GuardrailError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(AuthError)
async def auth_handler(_: Request, exc: AuthError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(NotFoundError)
async def not_found_handler(_: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(StateError)
async def state_handler(_: Request, exc: StateError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


# ---------------------------------------------------------------- who is calling?
def _token(authorization: Optional[str]) -> Optional[str]:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return None


def current_user(authorization: Optional[str] = Header(None)) -> dict:
    user = db.user_for_token(_token(authorization))
    if not user:
        raise HTTPException(401, "Please log in again.")
    return user


def own_session(session_id: str, user: dict):
    """A user can only touch their own debate."""
    s = coach.get(session_id)
    if (s.username or "").lower() != user["username"].lower():
        raise NotFoundError("Debate session not found.")
    return s


# ---------------------------------------------------------------- public endpoints
@app.get("/", tags=["system"])
def root():
    return {"app": "AI Debate Coach API", "docs": "/docs", "health": "/health"}


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "ai_mode": llm.active_mode(), "configured_mode": llm.AI_MODE,
            "ollama_model": llm.current_model()}


@app.get("/topics", tags=["debate"])
def topics():
    return all_topics()


# ---------------------------------------------------------------- accounts
@app.post("/auth/register", tags=["accounts"])
def register(body: RegisterIn):
    user = db.register(body.full_name, body.username, body.email, body.password)
    return {"token": db.create_token(user["id"]), "user": db.public(user)}


@app.post("/auth/login", tags=["accounts"])
def login(body: LoginIn):
    try:
        user = db.login(body.login, body.password)
    except AuthError as e:
        raise HTTPException(401, str(e))
    return {"token": db.create_token(user["id"]), "user": db.public(user)}


@app.post("/auth/logout", tags=["accounts"])
def logout(authorization: Optional[str] = Header(None)):
    db.delete_token(_token(authorization))
    return {"logged_out": True}


@app.get("/auth/me", tags=["accounts"])
def me(user: dict = Depends(current_user)):
    return db.public(user)


# ---------------------------------------------------------------- debates (logged-in users)
@app.post("/debates/start", tags=["debate"])
def start_debate(body: StartIn, user: dict = Depends(current_user)):
    s = coach.start(body.motion, body.side, body.difficulty, body.rounds, user["username"], body.category)
    return s.public()


@app.post("/debates/{session_id}/argue", tags=["debate"])
def argue(session_id: str, body: ArgueIn, user: dict = Depends(current_user)):
    own_session(session_id, user)
    return coach.argue(session_id, body.message).public()


@app.post("/debates/{session_id}/hint", tags=["debate"])
def hint(session_id: str, user: dict = Depends(current_user)):
    own_session(session_id, user)
    return coach.hint(session_id).public()


@app.post("/debates/{session_id}/end", tags=["debate"])
def end_debate(session_id: str, user: dict = Depends(current_user)):
    own_session(session_id, user)
    return coach.end(session_id).public()


@app.get("/debates/{session_id}", tags=["debate"])
def get_session(session_id: str, user: dict = Depends(current_user)):
    return own_session(session_id, user).public()


# ---------------------------------------------------------------- my history (Week 9)
@app.get("/me/history", tags=["history"])
def my_history(user: dict = Depends(current_user)):
    return db.list_debates(user["id"])


@app.get("/me/stats", tags=["history"])
def my_stats(user: dict = Depends(current_user)):
    return coach.stats(user["username"])


@app.get("/me/history/{debate_id}", tags=["history"])
def my_past_debate(debate_id: int, user: dict = Depends(current_user)):
    d = db.get_debate(debate_id)
    if not d or d["user_id"] != user["id"]:
        raise HTTPException(404, "Debate record not found.")
    return d


@app.delete("/me/history/{debate_id}", tags=["history"])
def delete_my_debate(debate_id: int, user: dict = Depends(current_user)):
    d = db.get_debate(debate_id)
    if not d or d["user_id"] != user["id"]:
        raise HTTPException(404, "Debate record not found.")
    db.delete_debate(debate_id)
    return {"deleted": debate_id}
