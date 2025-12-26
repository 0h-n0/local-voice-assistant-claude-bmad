"""Configuration management using Pydantic Settings"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="VOICE_ASSISTANT_",
        extra="ignore",
    )

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = ["http://localhost:3000"]

    # Logging
    log_level: str = "INFO"
    eval_log_path: Path = Path("logs/eval.jsonl")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> LogLevel:
        """Validate log level, fallback to INFO if invalid."""
        upper_v = v.upper()
        if upper_v not in VALID_LOG_LEVELS:
            return "INFO"
        return upper_v  # type: ignore[return-value]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance. Use this for dependency injection."""
    return Settings()


# For backward compatibility and simple imports
settings = get_settings()
