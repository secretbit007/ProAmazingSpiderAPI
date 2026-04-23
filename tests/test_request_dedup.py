from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _headers(sid: str) -> dict:
    return {"X-Session-ID": sid}


def test_duplicate_deal_replays_within_window():
    r = client.post("/api/v1/new-game", json={"difficulty": 5})
    assert r.status_code == 200
    sid = r.json()["session_id"]
    h = _headers(sid)

    first = client.post("/api/v1/deal", headers=h)
    assert first.status_code == 200
    state_after_first = client.get("/api/v1/game-state", headers=h).json()

    second = client.post("/api/v1/deal", headers=h)
    assert second.status_code == 200
    assert second.headers.get("X-Request-Dedup") == "replay"
    assert second.content == first.content

    state_after_second = client.get("/api/v1/game-state", headers=h).json()
    assert state_after_second == state_after_first
