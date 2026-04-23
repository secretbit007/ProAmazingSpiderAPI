from fastapi import APIRouter, HTTPException, Request
from app.core.game_logic import game_instance
from app.core.session_manager import session_manager
from app.schemas.game_state import GameState, MoveRequest, NewGameRequest, SessionResponse
from app.utils.logger import CardArrangementLogger
from typing import List

router = APIRouter()

@router.post("/new-game", response_model=SessionResponse)
async def new_game(request: NewGameRequest, http_request: Request):
    request_id = getattr(http_request.state, 'request_id', None)
    session_id = getattr(http_request.state, 'session_id', None)
    
    # Log operation start
    CardArrangementLogger.log_operation_start(
        "new_game", 
        {"difficulty": request.difficulty, "session_id": session_id}, 
        request_id
    )
    
    try:
        # Create new session if not provided
        if not session_id:
            session_id = session_manager.create_session()
        
        # Get or create game instance for this session
        game_instance = session_manager.get_session(session_id)
        if not game_instance:
            raise HTTPException(status_code=400, detail="Failed to create or retrieve session")

        session_manager.clear_dedup_cache(session_id)

        # Initialize new game
        game_instance.new_game(request.difficulty)
        game_state = game_instance.get_game_state()
        
        # Save session state
        session_manager.save_session(session_id)
        
        # Log the new game state
        CardArrangementLogger.log_game_state(game_state, "new_game", request_id)
        
        # Log operation success
        CardArrangementLogger.log_operation_end("new_game", True, None, request_id)
        
        return SessionResponse(session_id=session_id, game_state=game_state)
    except Exception as e:
        # Log operation failure
        CardArrangementLogger.log_operation_end("new_game", False, str(e), request_id)
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/game-state", response_model=GameState)
async def get_game_state(http_request: Request):
    request_id = getattr(http_request.state, 'request_id', None)
    session_id = getattr(http_request.state, 'session_id', None)
    
    # Log operation start
    CardArrangementLogger.log_operation_start("get_game_state", {"session_id": session_id}, request_id)
    
    try:
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID required")
        
        # Get game instance for this session
        game_instance = session_manager.get_session(session_id)
        if not game_instance:
            raise HTTPException(status_code=404, detail="Session not found or expired")
        
        game_state = game_instance.get_game_state()
        
        # Save session state
        session_manager.save_session(session_id)
        
        # Log the current game state
        CardArrangementLogger.log_game_state(game_state, "get_game_state", request_id)
        
        # Log operation success
        CardArrangementLogger.log_operation_end("get_game_state", True, None, request_id)
        
        return game_state
    except Exception as e:
        # Log operation failure
        CardArrangementLogger.log_operation_end("get_game_state", False, str(e), request_id)
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/move", response_model=List[GameState])
async def make_move(move: MoveRequest, http_request: Request):
    request_id = getattr(http_request.state, 'request_id', None)
    session_id = getattr(http_request.state, 'session_id', None)
    
    # Log operation start
    CardArrangementLogger.log_operation_start(
        "move", 
        {"from_row": move.from_row, "from_col": move.from_col, "to_row": move.to_row, "to_col": move.to_col, "session_id": session_id}, 
        request_id
    )
    
    # Log move operation details
    CardArrangementLogger.log_move_operation(
        move.from_row, move.from_col, move.to_row, move.to_col, request_id
    )
    
    try:
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID required")
        
        # Get game instance for this session
        game_instance = session_manager.get_session(session_id)
        if not game_instance:
            raise HTTPException(status_code=404, detail="Session not found or expired")
        
        # Get state before move
        before_state = game_instance.get_game_state()
        
        # Log the gameboard before move
        # CardArrangementLogger.log_game_state(before_state, "move_before", request_id)
        
        game_instance.cardfrontclick(
            rw=move.from_row,
            cl=move.from_col,
        )

        result = game_instance.states
        after_state = game_instance.get_game_state()
        result.append(after_state)
        
        # Save session state
        session_manager.save_session(session_id)
        
        # Log the gameboard after move
        CardArrangementLogger.log_game_state(after_state, "move_after", request_id)
        
        # Log state comparison
        CardArrangementLogger.log_state_comparison(before_state, after_state, "move", request_id)
        
        # Log operation success
        CardArrangementLogger.log_operation_end("move", True, None, request_id)
        
        return result
    except Exception as e:
        # Log operation failure
        CardArrangementLogger.log_operation_end("move", False, str(e), request_id)
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/deal", response_model=GameState)
async def deal_cards(http_request: Request):
    request_id = getattr(http_request.state, 'request_id', None)
    session_id = getattr(http_request.state, 'session_id', None)
    
    # Log operation start
    CardArrangementLogger.log_operation_start("deal", {"session_id": session_id}, request_id)
    
    try:
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID required")
        
        # Get game instance for this session
        game_instance = session_manager.get_session(session_id)
        if not game_instance:
            raise HTTPException(status_code=404, detail="Session not found or expired")
        
        # Get state before dealing
        before_state = game_instance.get_game_state()
        
        # Log the gameboard before dealing
        # CardArrangementLogger.log_game_state(before_state, "deal_before", request_id)
        
        game_instance.stackclick()
        after_state = game_instance.get_game_state()
        
        # Save session state
        session_manager.save_session(session_id)
        
        # Log the gameboard after dealing
        CardArrangementLogger.log_game_state(after_state, "deal_after", request_id)
        
        # Log state comparison
        CardArrangementLogger.log_state_comparison(before_state, after_state, "deal", request_id)
        
        # Log operation success
        CardArrangementLogger.log_operation_end("deal", True, None, request_id)
        
        return after_state
    except Exception as e:
        # Log operation failure
        CardArrangementLogger.log_operation_end("deal", False, str(e), request_id)
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/solve", response_model=List[GameState])
async def solve_game(http_request: Request):
    request_id = getattr(http_request.state, 'request_id', None)
    session_id = getattr(http_request.state, 'session_id', None)
    
    # Log operation start
    CardArrangementLogger.log_operation_start("solve", {"session_id": session_id}, request_id)
    
    try:
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID required")
        
        # Get game instance for this session
        game_instance = session_manager.get_session(session_id)
        if not game_instance:
            raise HTTPException(status_code=404, detail="Session not found or expired")
        
        # Get state before solving
        before_state = game_instance.get_game_state()
        
        # Log the gameboard before solving
        # CardArrangementLogger.log_game_state(before_state, "solve_before", request_id)
        
        game_instance.solve()

        result = game_instance.states
        after_state = game_instance.get_game_state()
        result.append(after_state)
        
        # Save session state
        session_manager.save_session(session_id)
        
        # Log the gameboard after solving
        CardArrangementLogger.log_game_state(after_state, "solve_after", request_id)
        
        # Log state comparison
        CardArrangementLogger.log_state_comparison(before_state, after_state, "solve", request_id)
        
        # Log operation success
        CardArrangementLogger.log_operation_end("solve", True, None, request_id)

        return result
    except Exception as e:
        # Log operation failure
        CardArrangementLogger.log_operation_end("solve", False, str(e), request_id)
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/undo", response_model=GameState)
async def undo_move(http_request: Request):
    request_id = getattr(http_request.state, 'request_id', None)
    session_id = getattr(http_request.state, 'session_id', None)
    
    # Log operation start
    CardArrangementLogger.log_operation_start("undo", {"session_id": session_id}, request_id)
    
    try:
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID required")
        
        # Get game instance for this session
        game_instance = session_manager.get_session(session_id)
        if not game_instance:
            raise HTTPException(status_code=404, detail="Session not found or expired")
        
        # Get state before undo
        before_state = game_instance.get_game_state()
        
        # Log the gameboard before undo
        # CardArrangementLogger.log_game_state(before_state, "undo_before", request_id)
        
        game_instance.undo()
        after_state = game_instance.get_game_state()
        
        # Save session state
        session_manager.save_session(session_id)
        
        # Log the gameboard after undo
        CardArrangementLogger.log_game_state(after_state, "undo_after", request_id)
        
        # Log state comparison
        CardArrangementLogger.log_state_comparison(before_state, after_state, "undo", request_id)
        
        # Log operation success
        CardArrangementLogger.log_operation_end("undo", True, None, request_id)
        
        return after_state
    except Exception as e:
        # Log operation failure
        CardArrangementLogger.log_operation_end("undo", False, str(e), request_id)
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/cleanup-sessions")
async def cleanup_sessions(http_request: Request):
    """Clean up expired sessions (admin endpoint)"""
    request_id = getattr(http_request.state, 'request_id', None)
    
    try:
        session_manager.cleanup_expired_sessions()
        return {"message": "Session cleanup completed"}
    except Exception as e:
        CardArrangementLogger.log_operation_end("cleanup_sessions", False, str(e), request_id)
        raise HTTPException(status_code=500, detail=str(e))