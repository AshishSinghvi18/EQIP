from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "EQIP Backend"
    app_version: str = "1.0.0"
    api_prefix: str = "/api"
    database_url: str = "sqlite:///./backend/eqip.db"
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )
    seed_demo_data: bool = True
    reset_demo_data: bool = False
    score_window_days: int = 180

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="EQIP_",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
