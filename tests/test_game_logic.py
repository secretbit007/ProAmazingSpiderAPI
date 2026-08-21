from app.core.game_logic import SpiderSolitaire
from app.core.daily import daily_seed


def _face_up_suits(game: SpiderSolitaire):
    suits = set()
    for col in range(10):
        row = game.rowbase
        while row < 80 and game.cardsarray[row, col, 0] != 0:
            rank = int(game.cardsarray[row, col, 0])
            if rank != game.facedown:
                suits.add(int(game.cardsarray[row, col, 1]))
            row += 1
    return suits


def test_new_game():
    game = SpiderSolitaire()
    game.new_game(5)
    state = game.get_game_state()
    assert len(state.piles) == 10
    assert state.difficulty == 5
    assert state.suit_count == 4


def test_seeded_deal_is_deterministic():
    a = SpiderSolitaire()
    b = SpiderSolitaire()
    a.new_game(4, suit_count=4, seed=12345)
    b.new_game(4, suit_count=4, seed=12345)
    assert a.cardsarray.tolist() == b.cardsarray.tolist()


def test_one_suit_deal():
    game = SpiderSolitaire()
    game.new_game(3, suit_count=1, seed=7)
    assert _face_up_suits(game) == {1}
    assert game.get_game_state().suit_count == 1


def test_two_suit_deal():
    game = SpiderSolitaire()
    game.new_game(3, suit_count=2, seed=7)
    assert _face_up_suits(game).issubset({1, 2})
    assert game.get_game_state().suit_count == 2


def test_hint_does_not_mutate_board():
    game = SpiderSolitaire()
    game.new_game(0, suit_count=1, seed=99)
    before = game.cardsarray.copy()
    hint = game.suggest_hint()
    assert game.cardsarray.tolist() == before.tolist()
    assert hint["reason"] in ("same_suit", "rank", "empty", "complete_suit", "none")


def test_daily_seed_stable():
    assert daily_seed("2026-08-22") == daily_seed("2026-08-22")
    assert daily_seed("2026-08-22") != daily_seed("2026-08-23")
