from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from app.core.config import settings
from app.api.v1.endpoints import router
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.session_middleware import SessionMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION
)

# Add session middleware (must be before logging middleware)
app.add_middleware(SessionMiddleware)

# Add logging middleware
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
