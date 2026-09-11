from fastapi.testclient import TestClient

from app.core.session_manager import session_manager
from app.main import app

client = TestClient(app)


def _headers(session_id):
    return {"X-Session-ID": session_id}


def _new_session(**kwargs):
    payload = {"difficulty": 0, "suit_count": 1, "seed": 1}
    payload.update(kwargs)
    created = client.post("/api/v1/new-game", json=payload)
    assert created.status_code == 200
    return created.json()["session_id"], created


def _set_col(game, col, cards):
    row = game.rowbase
    game.cardsarray[row:, col, :] = 0
    for rank, suit in cards:
        game.cardsarray[row, col, 0] = rank
        game.cardsarray[row, col, 1] = suit
        row += 1
    game.lastcard[col] = row - 1 if cards else game.rowbase - 1


def _layout_two_sevens(game):
    """6 of suit 2 can land on either 7; auto-pick prefers the same-suit 7 in col 1."""
    game.cardsarray[:, :, :] = 0
    game.lastcard[:] = game.rowbase - 1
    game.oldr = -1
    game.oldc = -1
    game.oldmasthead = -1
    game.colmoves[:] = 0
    game.historycount = 0
    _set_col(game, 0, [(7, 1)])
    _set_col(game, 1, [(7, 2)])
    _set_col(game, 2, [(6, 2)])
    for col in range(3, 10):
        _set_col(game, col, [(13, 1)])


def _pile_ranks(state, col):
    return [card["rank"] for card in state["piles"][col]["cards"] if card["is_face_up"]]


def test_new_game():
    response = client.post("/api/v1/new-game", json={"difficulty": 5})
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "game_state" in data
    assert "piles" in data["game_state"]
    assert data["game_state"]["suit_count"] == 4
    assert response.headers.get("x-session-id") == data["session_id"]


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
    game = session_manager.get_session(session_id)
    before_board = game.cardsarray.copy()
    before_history = int(game.historycount)
    before_oldr, before_oldc = int(game.oldr), int(game.oldc)

    hint = client.post("/api/v1/hint", headers=_headers(session_id))
    assert hint.status_code == 200
    body = hint.json()
    assert "reason" in body
    assert "message" in body

    state = client.get("/api/v1/game-state", headers=_headers(session_id))
    assert state.status_code == 200
    assert state.json()["completed_sequences"] == before["completed_sequences"]
    assert state.json()["moves"] == before["moves"]
    assert game.cardsarray.tolist() == before_board.tolist()
    assert int(game.historycount) == before_history
    assert int(game.oldr) == before_oldr
    assert int(game.oldc) == before_oldc


def test_new_game_reuses_session_and_restamps_deal_start():
    session_id, _ = _new_session()
    game = session_manager.get_session(session_id)
    game.deal_started_at = 1.0
    game.deal_completed_at = 99.0
    again = client.post(
        "/api/v1/new-game",
        headers=_headers(session_id),
        json={"difficulty": 0, "suit_count": 1, "seed": 2},
    )
    assert again.status_code == 200
    assert again.headers.get("x-session-id") == session_id
    assert again.json()["session_id"] == session_id
    assert game.deal_started_at != 1.0
    assert game.deal_started_at is not None
    assert game.deal_completed_at is None


def test_to_col_overrides_auto_pick():
    session_id, _ = _new_session()
    game = session_manager.get_session(session_id)
    _layout_two_sevens(game)

    moved = client.post(
        "/api/v1/move",
        headers=_headers(session_id),
        json={"from_row": 1, "from_col": 2, "to_col": 0},
    )
    assert moved.status_code == 200
    assert isinstance(moved.json(), list)
    final = moved.json()[-1]
    assert _pile_ranks(final, 0) == [7, 6]
    assert _pile_ranks(final, 1) == [7]
    assert _pile_ranks(final, 2) == []


def test_to_col_can_drop_on_empty_pile_and_moves_same_suit_run():
    session_id, _ = _new_session()
    game = session_manager.get_session(session_id)
    game.cardsarray[:, :, :] = 0
    game.lastcard[:] = game.rowbase - 1
    game.oldr = -1
    game.oldc = -1
    _set_col(game, 0, [(9, 2), (8, 2), (7, 2)])
    _set_col(game, 1, [])
    for col in range(2, 10):
        _set_col(game, col, [(13, 1)])

    moved = client.post(
        "/api/v1/move",
        headers=_headers(session_id),
        json={"from_row": 1, "from_col": 0, "to_col": 1},
    )
    assert moved.status_code == 200
    final = moved.json()[-1]
    assert _pile_ranks(final, 0) == []
    assert _pile_ranks(final, 1) == [9, 8, 7]


def test_same_column_drop_is_noop():
    session_id, _ = _new_session()
    game = session_manager.get_session(session_id)
    _layout_two_sevens(game)
    game.oldr = 4
    game.oldc = 9
    before_history = int(game.historycount)
    before_board = game.cardsarray.copy()

    moved = client.post(
        "/api/v1/move",
        headers=_headers(session_id),
        json={"from_row": 1, "from_col": 2, "to_col": 2},
    )
    assert moved.status_code == 200
    assert isinstance(moved.json(), list)
    assert int(game.historycount) == before_history
    assert game.cardsarray.tolist() == before_board.tolist()
    assert int(game.oldr) == 4
    assert int(game.oldc) == 9
    assert _pile_ranks(moved.json()[-1], 2) == [6]


def test_invalid_to_col_is_rejected_without_changing_tap_cycle():
    session_id, _ = _new_session()
    game = session_manager.get_session(session_id)
    _layout_two_sevens(game)
    game.oldr = 3
    game.oldc = 8
    game.oldmasthead = 2
    before_history = int(game.historycount)
    before_board = game.cardsarray.copy()

    moved = client.post(
        "/api/v1/move",
        headers=_headers(session_id),
        json={"from_row": 1, "from_col": 2, "to_col": 5},
    )
    assert moved.status_code == 400
    assert int(game.historycount) == before_history
    assert game.cardsarray.tolist() == before_board.tolist()
    assert int(game.oldr) == 3
    assert int(game.oldc) == 8
    assert int(game.oldmasthead) == 2


def test_tap_without_to_col_auto_picks_and_second_tap_cycles():
    session_id, _ = _new_session()
    game = session_manager.get_session(session_id)
    _layout_two_sevens(game)

    first = client.post(
        "/api/v1/move",
        headers=_headers(session_id),
        json={"from_row": 1, "from_col": 2},
    )
    assert first.status_code == 200
    after_first = first.json()[-1]
    assert _pile_ranks(after_first, 1) == [7, 6]
    assert _pile_ranks(after_first, 0) == [7]
    assert _pile_ranks(after_first, 2) == []

    second = client.post(
        "/api/v1/move",
        headers=_headers(session_id),
        json={"from_row": 2, "from_col": 1},
    )
    assert second.status_code == 200
    after_second = second.json()[-1]
    assert _pile_ranks(after_second, 0) == [7, 6]
    assert _pile_ranks(after_second, 1) == [7]


def test_invalid_tap_is_rejected():
    session_id, _ = _new_session()
    game = session_manager.get_session(session_id)
    _layout_two_sevens(game)
    before_history = int(game.historycount)

    moved = client.post(
        "/api/v1/move",
        headers=_headers(session_id),
        json={"from_row": 1, "from_col": 5},
    )
    assert moved.status_code == 400
    assert int(game.historycount) == before_history
    state = game.get_game_state()
    dumped = state.model_dump() if hasattr(state, "model_dump") else state.dict()
    assert _pile_ranks(dumped, 5) == [13]


def test_deal_rejects_empty_column_without_history_or_stock_change():
    session_id, _ = _new_session()
    game = session_manager.get_session(session_id)
    _set_col(game, 0, [])
    before_deal = int(game.dealnext10)
    before_history = int(game.historycount)
    before_next = int(game.nextcard)

    dealt = client.post("/api/v1/deal", headers=_headers(session_id))
    assert dealt.status_code == 400
    assert int(game.dealnext10) == before_deal
    assert int(game.historycount) == before_history
    assert int(game.nextcard) == before_next


def test_deal_rejects_empty_stock_without_history_or_stock_change():
    session_id, _ = _new_session()
    game = session_manager.get_session(session_id)
    game.dealnext10 = 5
    game.nextcard = 104
    before_history = int(game.historycount)

    dealt = client.post("/api/v1/deal", headers=_headers(session_id))
    assert dealt.status_code == 400
    assert int(game.dealnext10) == 5
    assert int(game.historycount) == before_history


def test_deal_happy_path_keeps_game_state_shape():
    session_id, created = _new_session()
    dealt = client.post("/api/v1/deal", headers=_headers(session_id))
    assert dealt.status_code == 200
    body = dealt.json()
    assert "piles" in body
    assert len(body["piles"]) == 10
    assert body["draws_remaining"] == created.json()["game_state"]["draws_remaining"] - 1
    assert body["stock_count"] == created.json()["game_state"]["stock_count"] - 10
