from app.core.game_logic import SpiderSolitaire


def test_new_game():
    game = SpiderSolitaire()
    game.new_game(5)
    state = game.get_game_state()
    assert len(state.piles) == 10
    assert state.difficulty == 5