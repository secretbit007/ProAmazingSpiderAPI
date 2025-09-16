import uuid
import json
from datetime import datetime
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging
from app.core.game_logic import game_instance
from app.utils.logger import CardArrangementLogger

logger = logging.getLogger('request_logger')

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to add request ID and logging context to each request"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Get client IP address
        client_ip = request.client.host if request.client else "unknown"
        
        # Log request start with current board state
        logger.info(f"Request started - ID: {request_id}, IP: {client_ip}, Method: {request.method}, Path: {request.url.path}")
        
        # Log current board state at request start (only if session exists)
        session_id = getattr(request.state, 'session_id', None)
        if session_id:
            try:
                from app.core.session_manager import session_manager
                game_instance = session_manager.get_session(session_id)
                if game_instance:
                    game_state = game_instance.get_game_state()
                    CardArrangementLogger.log_game_state(game_state, f"request_start_{request.method}_{request.url.path.replace('/', '_')}", request_id)
            except Exception as e:
                logger.warning(f"Could not log board state at request start: {e}")
        
        # Process request
        response = await call_next(request)
        
        # Log request end with final board state
        logger.info(f"Request completed - ID: {request_id}, IP: {client_ip}, Status: {response.status_code}")
        
        # Log final board state at request end (only if session exists)
        if session_id:
            try:
                from app.core.session_manager import session_manager
                game_instance = session_manager.get_session(session_id)
                if game_instance:
                    game_state = game_instance.get_game_state()
                    CardArrangementLogger.log_game_state(game_state, f"request_end_{request.method}_{request.url.path.replace('/', '_')}", request_id)
            except Exception as e:
                logger.warning(f"Could not log board state at request end: {e}")
        
        # Add request ID to response headers for debugging
        response.headers["X-Request-ID"] = request_id
        
        return response

