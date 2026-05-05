import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.api.v1.endpoints import router
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.session_middleware import SessionMiddleware
from app.middleware.dedup_middleware import RequestDedupMiddleware

log = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION
)


@app.exception_handler(Exception)
async def unhandled_exception_json(request: Request, exc: Exception) -> JSONResponse:
    """Return JSON for unexpected errors so API clients never get HTML/plain 500 pages."""
    log.exception("%s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "error_type": type(exc).__name__},
    )

# Dedup runs inside Session so request.state.session_id is set (Session added after Dedup).
app.add_middleware(RequestDedupMiddleware)
app.add_middleware(SessionMiddleware)
app.add_middleware(LoggingMiddleware)

app.include_router(router, prefix=settings.API_V1_STR)

templates = Jinja2Templates(directory="templates")

@app.get("/")
async def root():
    return {"message": "Spider Solitaire API"}

@app.get("/privacy")
async def privacy(request: Request):
    return templates.TemplateResponse(
        request=request, name="privacy.html"
    )
