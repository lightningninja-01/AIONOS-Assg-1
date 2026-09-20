"""
Application settings loaded from environment variables.
All secrets come from .env — never hard-coded in source.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Executive Productivity Agent"
    environment: str = "development"
    port: int = 8001

    # LLM — single model for all operations
    groq_api_key: str
    groq_model: str = "openai/gpt-oss-20b"
    groq_timeout: float = 30.0

    # Simulation
    simulated_today: str = "2026-09-23"  # YYYY-MM-DD

    # CORS
    cors_origins: str = "http://localhost:5174,http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
