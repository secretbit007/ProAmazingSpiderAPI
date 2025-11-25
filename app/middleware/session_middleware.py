import uuid
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging

logger = logging.getLogger(__name__)

class SessionMiddleware(BaseHTTPMiddleware):
    """Middleware to handle session identification for guest users"""
    
    async def dispatch(self, request: Request, call_next):
        # Extract session ID from headers or query parameters
        session_id = None
        
        # Check for session ID in headers
        session_id = request.headers.get("X-Session-ID")
        
        # If not in headers, check query parameters
        if not session_id:
            session_id = request.query_params.get("session_id")
        
        # # If still no session ID, check if this is a new game request
        # if not session_id and request.url.path.endswith("/new-game"):
        #     # For new game requests without session ID, we'll create one in the endpoint
        #     pass
        # elif not session_id:
        #     # For other requests without session ID, return error
        #     if request.url.path not in ["/", "/docs", "/openapi.json", "/redoc"]:
        #         raise HTTPException(
        #             status_code=400, 
        #             detail="Session ID required. Please start a new game or provide session_id in header or query parameter."
        #         )
        
        # Add session ID to request state
        request.state.session_id = session_id
        
        # Process request
        response = await call_next(request)
        
        # Add session ID to response headers if available
        if session_id:
            response.headers["X-Session-ID"] = session_id
        
        return response
