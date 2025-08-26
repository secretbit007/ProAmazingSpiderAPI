from fastapi import FastAPI, Request
from app.core.config import settings
from app.api.v1.endpoints import router
from app.middleware.logging_middleware import LoggingMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION
)

# Add logging middleware
app.add_middleware(LoggingMiddleware)

app.include_router(router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Spider Solitaire API"}