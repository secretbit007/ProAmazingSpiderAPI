from app.core.session_manager import session_manager
from app.core.leaderboard import store as leaderboard_store
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

DATE = "2026-08-22"
PLAYER = "player-test-001"


def _isolate(tmp_path):
    leaderboard_store._data_dir = tmp_path


def _start_daily():
    daily = client.get("/api/v1/daily", params={"date": DATE}).json()
    created = client.post(
        "/api/v1/new-game",
        json={
            "difficulty": daily["difficulty"],
            "suit_count": daily["suit_count"],
            "seed": daily["seed"],
        },
    )
    assert created.status_code == 200
    return created.json()["session_id"], daily


def _force_win(session_id: str, moves: int = 80) -> None:
    game = session_manager.get_session(session_id)
    assert game is not None
    game.removedsuit[0:8] = [1, 2, 3, 4, 1, 2, 3, 4]
    game.historycount = moves
    game.solve_events = []


def test_daily_board_empty(tmp_path):
    _isolate(tmp_path)
    response = client.get("/api/v1/leaderboard/daily", params={"date": DATE, "player_id": PLAYER})
    assert response.status_code == 200
    body = response.json()
    assert body["date"] == DATE
    assert body["entries"] == []
    assert body["you"] is None
    assert body["total"] == 0


def test_submit_requires_session(tmp_path):
    _isolate(tmp_path)
    response = client.post(
        "/api/v1/leaderboard/daily",
        json={
            "player_id": PLAYER,
            "nickname": "Normand",
            "elapsed_seconds": 400,
            "date": DATE,
        },
    )
    assert response.status_code == 400


def test_submit_rejects_unfinished_daily(tmp_path):
    _isolate(tmp_path)
    session_id, _ = _start_daily()
    response = client.post(
        "/api/v1/leaderboard/daily",
        headers={"X-Session-ID": session_id},
        json={
            "player_id": PLAYER,
            "nickname": "Normand",
            "elapsed_seconds": 400,
            "date": DATE,
        },
    )
    assert response.status_code == 400
    assert "Finish" in response.json()["detail"]


def test_submit_and_rank(tmp_path):
    _isolate(tmp_path)
    session_id, _ = _start_daily()
    _force_win(session_id, moves=80)
    posted = client.post(
        "/api/v1/leaderboard/daily",
        headers={"X-Session-ID": session_id},
        json={
            "player_id": PLAYER,
            "nickname": "Normand",
            "elapsed_seconds": 400,
            "date": DATE,
        },
    )
    assert posted.status_code == 200
    body = posted.json()
    assert body["total"] == 1
    assert body["you"]["rank"] == 1
    assert body["you"]["nickname"] == "Normand"
    assert body["entries"][0]["is_you"] is True
    expected = 10000 - 80 * 15 - 400 * 2
    assert body["you"]["score"] == expected

    worse_session, _ = _start_daily()
    _force_win(worse_session, moves=120)
    other = client.post(
        "/api/v1/leaderboard/daily",
        headers={"X-Session-ID": worse_session},
        json={
            "player_id": "player-test-002",
            "nickname": "Alex",
            "elapsed_seconds": 900,
            "date": DATE,
        },
    )
    assert other.status_code == 200
    ranked = other.json()
    assert ranked["total"] == 2
    assert ranked["entries"][0]["nickname"] == "Normand"
    assert ranked["you"]["rank"] == 2


def test_same_player_keeps_best_score(tmp_path):
    _isolate(tmp_path)
    first, _ = _start_daily()
    _force_win(first, moves=80)
    client.post(
        "/api/v1/leaderboard/daily",
        headers={"X-Session-ID": first},
        json={
            "player_id": PLAYER,
            "nickname": "Normand",
            "elapsed_seconds": 400,
            "date": DATE,
        },
    )
    second, _ = _start_daily()
    _force_win(second, moves=200)
    again = client.post(
        "/api/v1/leaderboard/daily",
        headers={"X-Session-ID": second},
        json={
            "player_id": PLAYER,
            "nickname": "Norm",
            "elapsed_seconds": 900,
            "date": DATE,
        },
    )
    body = again.json()
    assert body["total"] == 1
    assert body["you"]["moves"] == 80
    assert body["you"]["nickname"] == "Norm"


def test_solve_games_are_rejected(tmp_path):
    _isolate(tmp_path)
    session_id, _ = _start_daily()
    _force_win(session_id, moves=10)
    game = session_manager.get_session(session_id)
    game.solve_events = [{"type": "move"}]
    response = client.post(
        "/api/v1/leaderboard/daily",
        headers={"X-Session-ID": session_id},
        json={
            "player_id": PLAYER,
            "nickname": "Normand",
            "elapsed_seconds": 30,
            "date": DATE,
        },
    )
    assert response.status_code == 400
    assert "Solve" in response.json()["detail"]
