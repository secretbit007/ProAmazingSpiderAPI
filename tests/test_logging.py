import pytest
from app.utils.logger import CardArrangementLogger
from app.schemas.game_state import GameState, Card, Pile

def test_logger_creation():
    """Test that the logger can be created and used"""
    logger = CardArrangementLogger()
    assert logger is not None

def test_log_game_state(monkeypatch):
    """Test logging game state"""
    from app.core import config as config_module

    monkeypatch.setattr(config_module.settings, "ENABLE_CARD_LOGGING", True)
    # Create a simple game state for testing
    cards = [Card(rank=13, suit=1, is_face_up=True)]  # King of hearts
    pile = Pile(cards=cards, last_card_index=0)
    game_state = GameState(
        piles=[pile],
        stock=[],
        stock_count=0,
        completed_sequences=0,
        completed_sequences_by_suit={},
        moves=0,
        difficulty=1,
        draws_remaining=5,
    )

    # Test logging (should not raise exceptions)
    result = CardArrangementLogger.log_game_state(game_state, "test_operation", "test_request_id")
    assert result is not None

def test_log_operation_start(monkeypatch):
    """Test logging operation start"""
    from app.core import config as config_module

    monkeypatch.setattr(config_module.settings, "ENABLE_CARD_LOGGING", True)
    result = CardArrangementLogger.log_operation_start("test_operation", {"test": "data"}, "test_request_id")
    assert result is not None

def test_log_operation_end(monkeypatch):
    """Test logging operation end"""
    from app.core import config as config_module

    monkeypatch.setattr(config_module.settings, "ENABLE_CARD_LOGGING", True)
    result = CardArrangementLogger.log_operation_end("test_operation", True, None, "test_request_id")
    assert result is not None

def test_log_move_operation(monkeypatch):
    """Test logging move operation"""
    from app.core import config as config_module

    monkeypatch.setattr(config_module.settings, "ENABLE_CARD_LOGGING", True)
    result = CardArrangementLogger.log_move_operation(0, 1, 2, 3, "test_request_id")
    assert result is not None

