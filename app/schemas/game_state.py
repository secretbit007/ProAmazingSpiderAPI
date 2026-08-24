from pydantic import BaseModel, Field, field_validator, model_validator
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
    suit_count: int = 4
    seed: Optional[int] = None

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
    suit_count: int = 4
    seed: Optional[int] = None

    @field_validator("difficulty")
    @classmethod
    def clamp_difficulty(cls, value: int) -> int:
        return max(0, min(9, value))

    @field_validator("suit_count")
    @classmethod
    def validate_suit_count(cls, value: int) -> int:
        if value not in (1, 2, 4):
            raise ValueError("suit_count must be 1, 2, or 4")
        return value


class HintResponse(BaseModel):
    from_row: Optional[int] = None
    from_col: Optional[int] = None
    to_col: Optional[int] = None
    reason: str
    message: str


class DailyChallengeResponse(BaseModel):
    date: str
    seed: int
    difficulty: int
    suit_count: int
    label: str = "Daily Challenge"


class LeaderboardSubmitRequest(BaseModel):
    player_id: str
    nickname: str
    elapsed_seconds: int
    date: Optional[str] = None

    @field_validator("player_id")
    @classmethod
    def validate_player_id(cls, value: str) -> str:
        cleaned = value.strip()
        if not (8 <= len(cleaned) <= 64):
            raise ValueError("player_id must be 8-64 characters")
        if any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-" for ch in cleaned):
            raise ValueError("player_id has invalid characters")
        return cleaned

    @field_validator("nickname")
    @classmethod
    def validate_nickname(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if not cleaned or len(cleaned) > 20:
            raise ValueError("nickname must be 1-20 characters")
        allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .'_-")
        if any(ch not in allowed for ch in cleaned):
            raise ValueError("nickname has invalid characters")
        return cleaned

    @field_validator("elapsed_seconds")
    @classmethod
    def clamp_elapsed(cls, value: int) -> int:
        return max(0, min(24 * 3600, int(value)))


class LeaderboardEntryPublic(BaseModel):
    rank: int
    nickname: str
    score: int
    moves: int
    elapsed_seconds: int
    is_you: bool = False


class LeaderboardYou(BaseModel):
    rank: int
    nickname: str
    score: int
    moves: int
    elapsed_seconds: int


class LeaderboardResponse(BaseModel):
    date: str
    entries: List[LeaderboardEntryPublic] = Field(default_factory=list)
    you: Optional[LeaderboardYou] = None
    total: int = 0

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