from pydantic import BaseModel
from typing import List, Optional

class Card(BaseModel):
    rank: int
    suit: int
    is_face_up: bool
    id: str

class Pile(BaseModel):
    cards: List[Card]
    last_card_index: int

class GameState(BaseModel):
    piles: List[Pile]
    stock: List[Card]
    completed_sequences: int
    moves: int
    difficulty: int
    draws_remaining: int

class MoveRequest(BaseModel):
    from_row: int
    from_col: int
    to_row: Optional[int] = None
    to_col: Optional[int] = None

class NewGameRequest(BaseModel):
    difficulty: int = 9