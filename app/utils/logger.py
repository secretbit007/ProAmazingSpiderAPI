import logging
import json
from datetime import datetime
from typing import Dict, List, Any
from app.schemas.game_state import GameState, Card, Pile
from app.core.config import settings

# Configure logging based on settings
def setup_logging():
    """Setup logging configuration based on settings"""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create handlers
    file_handler = logging.FileHandler(settings.LOG_FILE)
    file_handler.setFormatter(formatter)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Configure card arrangement logger
    card_logger = logging.getLogger('card_arrangement')
    card_logger.setLevel(log_level)
    card_logger.handlers.clear()
    card_logger.addHandler(file_handler)
    card_logger.addHandler(console_handler)

    # Configure request logger to use same handlers
    request_logger = logging.getLogger('request_logger')
    request_logger.setLevel(log_level)
    request_logger.handlers.clear()
    request_logger.addHandler(file_handler)
    request_logger.addHandler(console_handler)
    
    return card_logger

logger = setup_logging()

class CardArrangementLogger:
    """Logger for tracking card arrangements in Spider Solitaire"""
    
    @staticmethod
    def _suit_to_letter(suit: int) -> str:
        # Based on tests, 1 corresponds to Hearts
        return {1: 'H', 2: 'S', 3: 'D', 4: 'C'}.get(suit, '?')

    @staticmethod
    def _card_str(card: Card) -> str:
        if not card.is_face_up:
            return 'XX'
        suit_letter = CardArrangementLogger._suit_to_letter(card.suit)
        return f"{suit_letter}{card.rank}"

    @staticmethod
    def _format_board(game_state: GameState) -> str:
        piles = game_state.piles
        num_cols = len(piles)
        max_rows = max((len(p.cards) for p in piles), default=0)

        def fmt_cell(s: str) -> str:
            return s.rjust(3)

        header = ' '.join(fmt_cell(f"P{i}") for i in range(num_cols))
        lines: List[str] = [header]

        for r in range(max_rows):
            row_cells: List[str] = []
            for c in range(num_cols):
                cards = piles[c].cards
                if r < len(cards):
                    row_cells.append(fmt_cell(CardArrangementLogger._card_str(cards[r])))
                else:
                    row_cells.append(fmt_cell(""))
            lines.append(' '.join(row_cells))

        return "\n".join(lines)

    @staticmethod
    def log_game_state(game_state: GameState, operation: str, request_id: str = None):
        """Log the current game state with card arrangements in a human-readable format"""
        if not settings.ENABLE_CARD_LOGGING:
            return None
        
        header = (
            f"[request_id={request_id}] operation={operation} "
            f"stock={len(game_state.stock)} completed={game_state.completed_sequences} "
            f"moves={game_state.moves} difficulty={game_state.difficulty} draws={game_state.draws_remaining}"
        )
        board = CardArrangementLogger._format_board(game_state)
        log_text = f"{header}\n{board}"
        logger.info(log_text)
        return log_text
    
    @staticmethod
    def log_move_operation(from_row: int, from_col: int, to_row: int = None, to_col: int = None, 
                          request_id: str = None):
        """Log move operation details in a human-readable format"""
        if not settings.ENABLE_CARD_LOGGING:
            return None
        
        log_text = (
            f"[request_id={request_id}] operation=move from=({from_row},{from_col}) to=({to_row},{to_col})"
        )
        logger.info(log_text)
        return log_text
    
    @staticmethod
    def log_operation_start(operation: str, request_data: Dict[str, Any] = None, 
                           request_id: str = None):
        """Log the start of an operation in a human-readable format"""
        if not settings.ENABLE_CARD_LOGGING:
            return None
        
        req = json.dumps(request_data) if request_data is not None else "{}"
        log_text = f"[request_id={request_id}] operation={operation} status=started request={req}"
        logger.info(log_text)
        return log_text
    
    @staticmethod
    def log_operation_end(operation: str, success: bool, error_message: str = None, 
                         request_id: str = None):
        """Log the end of an operation in a human-readable format"""
        if not settings.ENABLE_CARD_LOGGING:
            return None
        
        status = 'completed' if success else 'failed'
        err = f" error=\"{error_message}\"" if error_message else ""
        log_text = f"[request_id={request_id}] operation={operation} status={status}{err}"
        logger.info(log_text)
        return log_text
    
    @staticmethod
    def log_state_comparison(before_state: GameState, after_state: GameState, 
                           operation: str, request_id: str = None):
        """Log comparison between before and after states in a human-readable format"""
        if not settings.ENABLE_CARD_LOGGING:
            return None
        
        completed_sequences_change = after_state.completed_sequences - before_state.completed_sequences
        moves_change = after_state.moves - before_state.moves
        draws_remaining_change = after_state.draws_remaining - before_state.draws_remaining
        total_cards_before = sum(len(pile.cards) for pile in before_state.piles)
        total_cards_after = sum(len(pile.cards) for pile in after_state.piles)
        stock_change = len(after_state.stock) - len(before_state.stock)

        log_text = (
            f"[request_id={request_id}] operation={operation} state_change "
            f"completed_delta={completed_sequences_change} moves_delta={moves_change} "
            f"draws_delta={draws_remaining_change} total_cards_before={total_cards_before} "
            f"total_cards_after={total_cards_after} stock_delta={stock_change}"
        )
        logger.info(log_text)
        return log_text
