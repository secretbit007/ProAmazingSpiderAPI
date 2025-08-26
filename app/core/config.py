from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Spider Solitaire API"
    PROJECT_DESCRIPTION: str = "API for playing Spider Solitaire"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Logging configuration
    ENABLE_CARD_LOGGING: bool = True
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "card_arrangements.log"
    
    class Config:
        case_sensitive = True

settings = Settings()