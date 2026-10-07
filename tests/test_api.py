"""API endpoint tests (Week 4 Friday). Needs fastapi + httpx installed."""
import uuid

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402

client = TestClient(app)


def make_user():
    name = "u_" + uuid.uuid4().hex[:8]
    r = client.post("/auth/register", json={"full_name": "Test User", "username": name,
                                            "email": f"{name}@example.com", "password": "secret123"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}, name


def test_health_and_topics_are_public():
    assert client.get("/health").json()["ai_mode"] == "offline"
    assert "Technology" in client.get("/topics").json()


def test_login_logout():
    headers, name = make_user()
    assert client.get("/auth/me", headers=headers).json()["username"] == name
    r = client.post("/auth/login", json={"login": name, "password": "secret123"})
    assert r.status_code == 200
    assert client.post("/auth/login", json={"login": name, "password": "wrong-one"}).status_code == 401
    client.post("/auth/logout", headers=headers)
    assert client.get("/auth/me", headers=headers).status_code == 401


def test_debate_requires_login():
    r = client.post("/debates/start", json={"motion": "Plastic bags should be banned", "side": "for"})
    assert r.status_code == 401


def test_api_debate_flow():
    headers, _ = make_user()
    r = client.post("/debates/start", headers=headers, json={"motion": "Plastic bags should be banned",
                                                             "side": "against", "difficulty": "beginner", "rounds": 3})
    assert r.status_code == 200
    sid = r.json()["session_id"]
    for text in ["A ban hurts small traders because they lose income. For example, market sellers in Kano.",
                 "Even if drains block, better waste collection fixes that without a ban, which means jobs are saved.",
                 "In conclusion, a ban is unfair because poorer traders carry the cost."]:
        r = client.post(f"/debates/{sid}/argue", headers=headers, json={"message": text})
        assert r.status_code == 200
    assert r.json()["status"] == "finished"
    r = client.post(f"/debates/{sid}/end", headers=headers)
    assert r.status_code == 200 and r.json()["scorecard"]["overall_score"] > 0
    history = client.get("/me/history", headers=headers).json()
    assert len(history) == 1
    assert client.get("/me/stats", headers=headers).json()["total_debates"] == 1
    assert client.get(f"/me/history/{history[0]['id']}", headers=headers).status_code == 200


def test_users_cannot_touch_each_others_debates():
    alice, _ = make_user()
    bob, _ = make_user()
    sid = client.post("/debates/start", headers=alice,
                      json={"motion": "Plastic bags should be banned", "side": "for", "rounds": 3}).json()["session_id"]
    assert client.post(f"/debates/{sid}/argue", headers=bob, json={"message": "hijack attempt here"}).status_code == 404
    for t in ["Bags block drains because they never rot, for example in Lagos.",
              "Even if traders lose, cleaner streets help everyone, which means health improves.",
              "In conclusion, ban them because the harm is bigger."]:
        client.post(f"/debates/{sid}/argue", headers=alice, json={"message": t})
    client.post(f"/debates/{sid}/end", headers=alice)
    debate_id = client.get("/me/history", headers=alice).json()[0]["id"]
    assert client.get(f"/me/history/{debate_id}", headers=bob).status_code == 404
    assert client.get("/me/history", headers=bob).json() == []


def test_api_errors():
    headers, _ = make_user()
    assert client.post("/debates/start", headers=headers,
                       json={"motion": "Plastic bags should be banned", "side": "sideways"}).status_code == 400
    assert client.post("/debates/missing/argue", headers=headers, json={"message": "hello"}).status_code == 404
    sid = client.post("/debates/start", headers=headers,
                      json={"motion": "Plastic bags should be banned", "side": "for"}).json()["session_id"]
    assert client.post(f"/debates/{sid}/argue", headers=headers, json={"message": ""}).status_code == 400
    assert client.post(f"/debates/{sid}/end", headers=headers).status_code == 409
