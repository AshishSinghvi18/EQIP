from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./eqip.db"
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # LLM settings (OpenAI-compatible API for open-weight models)
    LLM_API_BASE_URL: str = "http://localhost:11434/v1"  # e.g. Ollama, vLLM, OpenRouter
    LLM_API_KEY: str = ""  # API key for the LLM provider
    LLM_MODEL_NAME: str = "qwen3"  # Default model for RCA suggestions
    LLM_TIMEOUT: int = 30  # seconds

    # Embedding settings (for semantic search via pgvector)
    EMBEDDING_API_BASE_URL: str = "http://localhost:11434/v1"
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_MODEL_NAME: str = "bge-m3"  # BGE-M3, 1024 dimensions
    EMBEDDING_DIMENSIONS: int = 1024

    class Config:
        env_file = ".env"


settings = Settings()
