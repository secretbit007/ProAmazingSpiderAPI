from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Spider Solitaire API"
    PROJECT_DESCRIPTION: str = "API for playing Spider Solitaire"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Logging configuration (off by default: avoids heavy board dumps and duplicate get_game_state work)
    ENABLE_CARD_LOGGING: bool = False
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "card_arrangements.log"

    # Deduplicate rapid identical mutating requests (same session, body, game revision)
    ENABLE_REQUEST_DEDUP: bool = True
    # If the same POST is seen again while the board revision (historycount) is unchanged
    # since the last cached response, replay that response instead of re-running the handler.
    DEDUP_WINDOW_SECONDS: float = 0.75
    
    class Config:
        case_sensitive = True

settings = Settings()