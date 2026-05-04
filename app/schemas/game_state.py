from pydantic import BaseModel
from typing import List, Optional, Dict

class Card(BaseModel):
    rank: int
    suit: int
    is_face_up: bool

class Pile(BaseModel):
    cards: List[Card]
    last_card_index: int

class GameState(BaseModel):
    piles: List[Pile]
    stock: List[Card]
    completed_sequences: int
    completed_sequences_by_suit: Dict[int, int]  # suit -> count mapping
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

class SessionRequest(BaseModel):
    session_id: Optional[str] = None

class SessionResponse(BaseModel):
    session_id: str
    game_state: GameState


class SolveEvent(BaseModel):
    type: str
    from_row: Optional[int] = None
    from_col: Optional[int] = None
    to_row: Optional[int] = None
    to_col: Optional[int] = None
    rank: Optional[int] = None
    suit: Optional[int] = None


class SolveResponse(BaseModel):
    initial_state: GameState
    events: List[SolveEvent]
    final_state: GameState