from ..app.core.game_logic import SpiderSolitaire

def test_new_game():
    game = SpiderSolitaire()
    state = game.new_game()
    assert len(state.columns) == 10
    assert state.difficulty == 9