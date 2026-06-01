import os
from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = "Local AI Assistant Backend"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Ollama Configuration
    # Defaults to local fallback, but easily overriden by environment variables
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_TIMEOUT_SECONDS: float = float(os.getenv("OLLAMA_TIMEOUT", "60.0"))

settings = Settings()