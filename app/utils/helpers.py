import random
from typing import List, Any

def shuffle_list(items: List[Any]) -> List[Any]:
    """Shuffle a list in place and return it"""
    random.shuffle(items)
    return items

def validate_move(cards: List[Any], to_pile: List[Any]) -> bool:
    """
    Validate if cards can be moved to the destination pile.
    Simplified version - actual validation is in game logic.
    """
    if not cards:
        return False
    if not to_pile:
        return cards[0].rank == 13  # Only kings can be moved to empty pile
    return cards[-1].rank == to_pile[-1].rank - 1