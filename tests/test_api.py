from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_new_game():
    response = client.post("/api/v1/new-game", json={"difficulty": 5})
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "game_state" in data
    assert "piles" in data["game_state"]
    assert data["game_state"]["suit_count"] == 4


def test_get_game_state_requires_session():
    response = client.get("/api/v1/game-state")
    assert response.status_code == 400


def test_daily_challenge():
    response = client.get("/api/v1/daily", params={"date": "2026-08-22"})
    assert response.status_code == 200
    data = response.json()
    assert data["date"] == "2026-08-22"
    assert data["suit_count"] == 2
    assert isinstance(data["seed"], int)

    again = client.get("/api/v1/daily", params={"date": "2026-08-22"})
    assert again.json()["seed"] == data["seed"]


def test_hint_requires_session():
    response = client.post("/api/v1/hint")
    assert response.status_code == 400


def test_new_game_with_suits_and_hint():
    created = client.post(
        "/api/v1/new-game",
        json={"difficulty": 0, "suit_count": 1, "seed": 42},
    )
    assert created.status_code == 200
    session_id = created.json()["session_id"]
    before = created.json()["game_state"]

    hint = client.post("/api/v1/hint", headers={"X-Session-ID": session_id})
    assert hint.status_code == 200
    body = hint.json()
    assert "reason" in body
    assert "message" in body

    state = client.get("/api/v1/game-state", headers={"X-Session-ID": session_id})
    assert state.status_code == 200
    assert state.json()["completed_sequences"] == before["completed_sequences"]
    assert state.json()["moves"] == before["moves"]