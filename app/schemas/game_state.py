from pydantic import BaseModel, Field, model_validator
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
    # Wire format: prefer stock_count; legacy clients may send a long placeholder stock list.
    stock: List[Card] = Field(default_factory=list)
    stock_count: int = 0
    completed_sequences: int
    completed_sequences_by_suit: Dict[int, int] = Field(default_factory=dict)
    moves: int
    difficulty: int
    draws_remaining: int

    @model_validator(mode="after")
    def normalize_stock_wire_format(self) -> "GameState":
        st = self.stock
        sc = self.stock_count
        if len(st) > 0:
            if sc == 0:
                object.__setattr__(self, "stock_count", len(st))
            object.__setattr__(self, "stock", [])
        return self

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
    # One frame per solve step (server truth); clients should animate this instead of replaying events.
    state_sequence: List[GameState] = Field(default_factory=list)