import os
import json
import uuid
import time
import copy
import numpy as np
from typing import Any, Dict, Optional
from pathlib import Path
from app.core.game_logic import SpiderSolitaire
from app.schemas.game_state import GameState
import logging

logger = logging.getLogger(__name__)


def _completed_suit_count(game_instance: SpiderSolitaire) -> int:
    return int(sum(1 for suit in game_instance.removedsuit if int(suit) > 0))


def snapshot_play_state(game_instance: SpiderSolitaire) -> Dict[str, Any]:
    """Capture board, history, tap-cycle, timer, and solve-ban state for rollback."""
    return {
        "internal": game_instance.export_internal_state(),
        "solve_events": copy.deepcopy(getattr(game_instance, "solve_events", [])),
        "deal_started_at": getattr(game_instance, "deal_started_at", None),
        "deal_completed_at": getattr(game_instance, "deal_completed_at", None),
        "masthead": getattr(game_instance, "masthead", None),
    }


def restore_play_state(game_instance: SpiderSolitaire, snap: Dict[str, Any]) -> None:
    game_instance.import_internal_state(snap["internal"])
    game_instance.solve_events = copy.deepcopy(snap.get("solve_events") or [])
    game_instance.deal_started_at = snap.get("deal_started_at")
    game_instance.deal_completed_at = snap.get("deal_completed_at")
    if snap.get("masthead") is not None:
        game_instance.masthead = snap["masthead"]


def board_and_history_unchanged(game_instance: SpiderSolitaire, snap: Dict[str, Any]) -> bool:
    before = snap.get("internal") or {}
    before_board = np.array(before.get("cardsarray", []), dtype="int32")
    return (
        np.array_equal(game_instance.cardsarray, before_board)
        and int(game_instance.historycount) == int(before.get("historycount", 0))
        and int(game_instance.dealnext10) == int(before.get("dealnext10", 0))
        and int(game_instance.nextcard) == int(before.get("nextcard", 0))
    )


def sync_deal_timer(game_instance: SpiderSolitaire) -> None:
    """Stop the deal clock when the eighth suit comes off; resume if undone."""
    if _completed_suit_count(game_instance) >= 8:
        if getattr(game_instance, "deal_completed_at", None) is None:
            game_instance.deal_completed_at = time.time()
    else:
        game_instance.deal_completed_at = None


def apply_session_extras(game_instance: SpiderSolitaire, extras: Optional[dict]) -> None:
    if not extras:
        return
    if "deal_started_at" in extras:
        game_instance.deal_started_at = extras.get("deal_started_at")
    if "deal_completed_at" in extras:
        game_instance.deal_completed_at = extras.get("deal_completed_at")
    if "solve_events" in extras and extras.get("solve_events") is not None:
        game_instance.solve_events = copy.deepcopy(extras.get("solve_events") or [])
    if extras.get("masthead") is not None:
        game_instance.masthead = extras.get("masthead")


def collect_session_extras(game_instance: SpiderSolitaire) -> dict:
    return {
        "deal_started_at": getattr(game_instance, "deal_started_at", None),
        "deal_completed_at": getattr(game_instance, "deal_completed_at", None),
        "solve_events": copy.deepcopy(getattr(game_instance, "solve_events", [])),
        "masthead": getattr(game_instance, "masthead", None),
    }

class SessionManager:
    """Manages game sessions for guest users with file-based storage"""
    
    def __init__(self, sessions_dir: str = "sessions"):
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(exist_ok=True)
        self.active_sessions: Dict[str, SpiderSolitaire] = {}
        self.session_timeout = 3600  # 1 hour in seconds

    def create_session(self) -> str:
        """Create a new game session and return session ID"""
        session_id = str(uuid.uuid4())
        
        # Create new game instance
        game_instance = SpiderSolitaire()
        
        # Store in memory for active sessions
        self.active_sessions[session_id] = game_instance
        
        # Create session file
        session_file = self.sessions_dir / f"{session_id}.json"
        session_data = {
            "session_id": session_id,
            "created_at": time.time(),
            "last_accessed": time.time(),
            "game_initialized": False
        }
        
        with open(session_file, 'w') as f:
            json.dump(session_data, f)
        
        logger.info(f"Created new session: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[SpiderSolitaire]:
        """Get game instance for session, loading from file if needed"""
        if not session_id:
            return None
            
        # Check if session is in memory
        if session_id in self.active_sessions:
            self._update_session_access_time(session_id)
            return self.active_sessions[session_id]
        
        # Try to load from file
        session_file = self.sessions_dir / f"{session_id}.json"
        if not session_file.exists():
            logger.warning(f"Session file not found: {session_id}")
            return None
        
        try:
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            # Check if session has expired
            if self._is_session_expired(session_data):
                logger.info(f"Session expired: {session_id}")
                self._cleanup_session(session_id)
                return None
            
            # Create new game instance and restore state if available
            game_instance = SpiderSolitaire()
            
            # Try to restore game state from file
            game_state_file = self.sessions_dir / f"{session_id}_game.json"
            game_data = None
            if game_state_file.exists():
                try:
                    with open(game_state_file, 'r') as f:
                        game_data = json.load(f)
                    self._restore_game_state(game_instance, game_data)
                except Exception as e:
                    logger.warning(f"Failed to restore game state for session {session_id}: {e}")

            extras = {}
            extras.update({k: session_data[k] for k in (
                "deal_started_at", "deal_completed_at", "solve_events", "masthead"
            ) if k in session_data})
            if isinstance(game_data, dict):
                extras.update({k: game_data[k] for k in (
                    "deal_started_at", "deal_completed_at", "solve_events", "masthead"
                ) if k in game_data})
            apply_session_extras(game_instance, extras)
            
            # Store in memory
            self.active_sessions[session_id] = game_instance
            
            # Update access time
            self._update_session_access_time(session_id)
            
            logger.info(f"Restored session from file: {session_id}")
            return game_instance
            
        except Exception as e:
            logger.error(f"Error loading session {session_id}: {e}")
            return None
    
    def save_session(self, session_id: str) -> bool:
        """Save current game state to file"""
        if session_id not in self.active_sessions:
            return False
        
        try:
            game_instance = self.active_sessions[session_id]
            sync_deal_timer(game_instance)
            extras = collect_session_extras(game_instance)
            game_state = game_instance.get_game_state()
            
            # Save game state to file
            game_state_file = self.sessions_dir / f"{session_id}_game.json"
            game_data = {
                "game_state": game_state.dict(),
                "internal_state": self._extract_internal_state(game_instance),
                "saved_at": time.time(),
            }
            game_data.update(extras)
            
            with open(game_state_file, 'w') as f:
                json.dump(game_data, f, default=str)

            self._write_session_extras(session_id, extras)
            
            # Update session access time
            self._update_session_access_time(session_id)
            
            logger.debug(f"Saved game state for session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving session {session_id}: {e}")
            return False
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions from memory and filesystem"""
        current_time = time.time()
        expired_sessions = []
        
        # Check active sessions
        for session_id in list(self.active_sessions.keys()):
            session_file = self.sessions_dir / f"{session_id}.json"
            if session_file.exists():
                try:
                    with open(session_file, 'r') as f:
                        session_data = json.load(f)
                    if self._is_session_expired(session_data):
                        expired_sessions.append(session_id)
                except:
                    expired_sessions.append(session_id)
            else:
                expired_sessions.append(session_id)
        
        # Clean up expired sessions
        for session_id in expired_sessions:
            self._cleanup_session(session_id)
    
    def _is_session_expired(self, session_data: dict) -> bool:
        """Check if session has expired based on last access time"""
        last_accessed = session_data.get('last_accessed', 0)
        return (time.time() - last_accessed) > self.session_timeout
    
    def _update_session_access_time(self, session_id: str):
        """Update the last accessed time for a session"""
        session_file = self.sessions_dir / f"{session_id}.json"
        if session_file.exists():
            try:
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                session_data['last_accessed'] = time.time()
                with open(session_file, 'w') as f:
                    json.dump(session_data, f)
            except Exception as e:
                logger.warning(f"Failed to update access time for session {session_id}: {e}")

    def _write_session_extras(self, session_id: str, extras: dict) -> None:
        session_file = self.sessions_dir / f"{session_id}.json"
        if not session_file.exists():
            return
        try:
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            session_data.update(extras)
            with open(session_file, 'w') as f:
                json.dump(session_data, f, default=str)
        except Exception as e:
            logger.warning(f"Failed to persist session extras for {session_id}: {e}")
    
    def _cleanup_session(self, session_id: str):
        """Remove session from memory and filesystem"""
        # Remove from memory
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        
        # Remove files
        session_file = self.sessions_dir / f"{session_id}.json"
        game_state_file = self.sessions_dir / f"{session_id}_game.json"
        
        try:
            if session_file.exists():
                session_file.unlink()
            if game_state_file.exists():
                game_state_file.unlink()
            logger.info(f"Cleaned up session: {session_id}")
        except Exception as e:
            logger.error(f"Error cleaning up session {session_id}: {e}")
    
    def _extract_internal_state(self, game_instance: SpiderSolitaire) -> dict:
        """Extract internal game state for restoration"""
        return game_instance.export_internal_state()
    
    def _restore_game_state(self, game_instance: SpiderSolitaire, game_data: dict):
        """Restore game state from saved data"""
        try:
            internal_state = game_data.get("internal_state", {})
            game_instance.import_internal_state(internal_state)
            
            # Restore states history if present (legacy saves)
            if "states" in internal_state:
                from app.schemas.game_state import GameState
                game_instance.states = [GameState(**state) for state in internal_state["states"]]

            apply_session_extras(game_instance, game_data)
            
        except Exception as e:
            logger.error(f"Error restoring game state: {e}")
            # If restoration fails, the game will start fresh
            apply_session_extras(game_instance, game_data)

# Global session manager instance
session_manager = SessionManager()
