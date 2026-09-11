from fastapi import APIRouter, HTTPException, Request, Response
from app.core.game_logic import SpiderSolitaire
from app.core.session_manager import (
    board_and_history_unchanged,
    restore_play_state,
    session_manager,
    snapshot_play_state,
)
from app.core.daily import DAILY_DIFFICULTY, DAILY_SUIT_COUNT, daily_seed, parse_date
from app.core.leaderboard import MAX_ELAPSED_SECONDS, store as leaderboard_store
from app.schemas.game_state import (
    DailyChallengeResponse,
    GameState,
    HintResponse,
    LeaderboardResponse,
    LeaderboardSubmitRequest,
    MoveRequest,
    NewGameRequest,
    SessionResponse,
    SolveResponse,
)
from app.utils.logger import CardArrangementLogger
from typing import List, Optional
import time

router = APIRouter()


def _tableau_has_empty_column(game: SpiderSolitaire) -> bool:
    for col in range(10):
        if int(game.cardsarray[game.rowbase, col, 0]) == 0:
            return True
    return False


def _stock_is_empty(game: SpiderSolitaire) -> bool:
    return int(game.dealnext10) >= 5 or int(game.nextcard) >= 104


def _elapsed_from_session(game: SpiderSolitaire) -> int:
    started = getattr(game, "deal_started_at", None)
    if started is None:
        raise HTTPException(status_code=400, detail="Deal start time is not present")
    finished = getattr(game, "deal_completed_at", None)
    if finished is None:
        raise HTTPException(status_code=400, detail="Deal start time is not present")
    elapsed = int(round(max(0, float(finished) - float(started))))
    return max(0, min(MAX_ELAPSED_SECONDS, elapsed))


@router.post("/new-game", response_model=SessionResponse)
async def new_game(request: NewGameRequest, http_request: Request, response: Response):
    request_id = getattr(http_request.state, 'request_id', None)
    session_id = getattr(http_request.state, 'session_id', None)
    
    # Log operation start
    CardArrangementLogger.log_operation_start(
        "new_game", 
        {"difficulty": request.difficulty, "suit_count": request.suit_count, "seed": request.seed, "session_id": session_id}, 
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

        # Initialize new game
        game_instance.new_game(request.difficulty, request.suit_count, request.seed)
        game_instance.deal_started_at = time.time()
        game_instance.deal_completed_at = None
        game_state = game_instance.get_game_state()
        
        # Save session state
        session_manager.save_session(session_id)
        
        # Log the new game state
        CardArrangementLogger.log_game_state(game_state, "new_game", request_id)
        
        # Log operation success
        CardArrangementLogger.log_operation_end("new_game", True, None, request_id)

        response.headers["X-Session-ID"] = session_id
        return SessionResponse(session_id=session_id, game_state=game_state)
    except HTTPException:
        raise
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
        
        # Read-only: do not persist full game JSON on every poll (session access time still updated in get_session).
        
        # Log the current game state
        CardArrangementLogger.log_game_state(game_state, "get_game_state", request_id)
        
        # Log operation success
        CardArrangementLogger.log_operation_end("get_game_state", True, None, request_id)
        
        return game_state
    except HTTPException:
        raise
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

        if move.from_col < 0 or move.from_col > 9:
            raise HTTPException(status_code=400, detail="Invalid move")
        if move.to_col is not None and (move.to_col < 0 or move.to_col > 9):
            raise HTTPException(status_code=400, detail="Invalid move")

        # Dropping a card back onto its own pile is a no-op: keep the board and skip history.
        if move.to_col is not None and move.to_col == move.from_col:
            after_state = game_instance.get_game_state()
            CardArrangementLogger.log_operation_end("move", True, None, request_id)
            return [after_state]
        
        # Get state before move
        before_state = game_instance.get_game_state()
        
        # Log the gameboard before move
        # CardArrangementLogger.log_game_state(before_state, "move_before", request_id)

        snap = snapshot_play_state(game_instance)
        original_repeatcol = game_instance.repeatcol
        try:
            # Honor an explicit drop target instead of auto-pick.
            if move.to_col is not None:
                dest = int(move.to_col)

                def _forced_repeatcol(_dest=dest):
                    return _dest

                game_instance.repeatcol = _forced_repeatcol
            game_instance.cardfrontclick(
                rw=move.from_row,
                cl=move.from_col,
            )
        finally:
            game_instance.repeatcol = original_repeatcol

        if board_and_history_unchanged(game_instance, snap):
            restore_play_state(game_instance, snap)
            raise HTTPException(status_code=400, detail="Invalid move")

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
    except HTTPException:
        raise
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

        if _stock_is_empty(game_instance):
            raise HTTPException(status_code=400, detail="Stock is empty")
        if _tableau_has_empty_column(game_instance):
            raise HTTPException(status_code=400, detail="Cannot deal while a tableau column is empty")
        
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
    except HTTPException:
        raise
    except Exception as e:
        # Log operation failure
        CardArrangementLogger.log_operation_end("deal", False, str(e), request_id)
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/solve", response_model=SolveResponse)
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
        after_state = game_instance.get_game_state()
        
        # Save session state
        session_manager.save_session(session_id)
        
        # Log the gameboard after solving
        CardArrangementLogger.log_game_state(after_state, "solve_after", request_id)
        
        # Log state comparison
        CardArrangementLogger.log_state_comparison(before_state, after_state, "solve", request_id)
        
        # Log operation success
        CardArrangementLogger.log_operation_end("solve", True, None, request_id)

        state_sequence = [before_state, *game_instance.solve_snapshots]
        if state_sequence:
            state_sequence[-1] = after_state

        return SolveResponse(
            initial_state=before_state,
            events=game_instance.solve_events,
            final_state=after_state,
            state_sequence=state_sequence,
        )
    except HTTPException:
        raise
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
    except HTTPException:
        raise
    except Exception as e:
        # Log operation failure
        CardArrangementLogger.log_operation_end("undo", False, str(e), request_id)
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/hint", response_model=HintResponse)
async def get_hint(http_request: Request):
    request_id = getattr(http_request.state, 'request_id', None)
    session_id = getattr(http_request.state, 'session_id', None)

    CardArrangementLogger.log_operation_start("hint", {"session_id": session_id}, request_id)

    try:
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID required")

        game_instance = session_manager.get_session(session_id)
        if not game_instance:
            raise HTTPException(status_code=404, detail="Session not found or expired")

        snap = snapshot_play_state(game_instance)
        hint = game_instance.suggest_hint()
        restore_play_state(game_instance, snap)
        CardArrangementLogger.log_operation_end("hint", True, None, request_id)
        return HintResponse(**hint)
    except HTTPException:
        raise
    except Exception as e:
        CardArrangementLogger.log_operation_end("hint", False, str(e), request_id)
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/daily", response_model=DailyChallengeResponse)
async def get_daily_challenge(date: Optional[str] = None):
    try:
        date_str = parse_date(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD")

    return DailyChallengeResponse(
        date=date_str,
        seed=daily_seed(date_str),
        difficulty=DAILY_DIFFICULTY,
        suit_count=DAILY_SUIT_COUNT,
    )


@router.get("/leaderboard/daily", response_model=LeaderboardResponse)
async def get_daily_leaderboard(date: Optional[str] = None, player_id: Optional[str] = None):
    try:
        date_str = parse_date(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD")
    return LeaderboardResponse(**leaderboard_store.as_response(date_str, player_id))


@router.post("/leaderboard/daily", response_model=LeaderboardResponse)
async def submit_daily_score(body: LeaderboardSubmitRequest, http_request: Request):
    try:
        date_str = parse_date(body.date)
    except ValueError:
        raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD")

    session_id = getattr(http_request.state, "session_id", None)
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID required")

    game_instance = session_manager.get_session(session_id)
    if not game_instance:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    if getattr(game_instance, "solve_events", None):
        raise HTTPException(status_code=400, detail="Solve games are not posted to the daily board")

    state = game_instance.get_game_state()
    if (
        state.seed != daily_seed(date_str)
        or state.difficulty != DAILY_DIFFICULTY
        or state.suit_count != DAILY_SUIT_COUNT
    ):
        raise HTTPException(status_code=400, detail="This game is not the Daily Challenge for that date")
    if state.completed_sequences < 8:
        raise HTTPException(status_code=400, detail="Finish the Daily Challenge before posting a score")

    elapsed = _elapsed_from_session(game_instance)

    return LeaderboardResponse(
        **leaderboard_store.submit(
            date_str,
            body.player_id,
            body.nickname,
            state.moves,
            elapsed,
        )
    )


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