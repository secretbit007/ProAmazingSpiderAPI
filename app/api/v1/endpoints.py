from fastapi import APIRouter, HTTPException
from app.core.game_logic import game_instance
from app.schemas.game_state import GameState, MoveRequest, NewGameRequest
from typing import List
from time import sleep

router = APIRouter()

@router.post("/new-game", response_model=GameState)
async def new_game(request: NewGameRequest):
    try:
        game_instance.new_game(request.difficulty)
        return game_instance.get_game_state()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/game-state", response_model=GameState)
async def get_game_state():
    return game_instance.get_game_state()

@router.post("/move", response_model=List[GameState])
async def make_move(move: MoveRequest):
    try:
        game_instance.cardfrontclick(
            rw=move.from_row,
            cl=move.from_col,
        )
        
        return game_instance.states
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/deal", response_model=GameState)
async def deal_cards():
    try:
        game_instance.stackclick()
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
        game_instance.undo()
        return game_instance.get_game_state()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))