from fastapi import APIRouter, HTTPException
from app.core.game_logic import game_instance
from app.schemas.game_state import GameState, MoveRequest, NewGameRequest

router = APIRouter()

@router.post("/new-game", response_model=GameState)
async def new_game(request: NewGameRequest):
    try:
        return game_instance.new_game(request.difficulty)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/game-state", response_model=GameState)
async def get_game_state():
    return game_instance.get_game_state()

@router.post("/move", response_model=GameState)
async def make_move(move: MoveRequest):
    try:
        game_instance.auto_move(
            from_row=move.from_row,
            from_col=move.from_col,
        )
        return game_instance.get_game_state()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/deal", response_model=GameState)
async def deal_cards():
    try:
        game_instance.deal_cards()
        return game_instance.get_game_state()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/solve", response_model=GameState)
async def solve_game():
    try:
        game_instance.solve()
        return game_instance.get_game_state()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/undo", response_model=GameState)
async def undo_move():
    try:
        game_instance.undo_move()
        return game_instance.get_game_state()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))