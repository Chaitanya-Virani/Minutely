"""Application configuration loaded from environment variables.

Exposes a `Settings` BaseSettings class, a module-level `settings` singleton,
and a `get_settings()` accessor suitable for use with FastAPI's `Depends`.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated, List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed runtime settings for the Minutely backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    ANTHROPIC_API_KEY: str = Field(
        default="",
        description="Secret API key for the Anthropic Claude API.",
    )
    CLAUDE_MODEL: str = Field(
        default="claude-sonnet-4-20250514",
        description="Anthropic model identifier used for report generation.",
    )
    MAX_FILE_SIZE_MB: int = Field(
        default=25,
        ge=1,
        description="Maximum accepted upload size per file, in megabytes.",
    )
    CORS_ORIGINS: Annotated[List[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000"],
        description="Allowed CORS origins. Accepts a comma-separated string in env.",
    )
    PORT: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Port the HTTP server binds to (Railway injects this at runtime).",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _split_cors_origins(cls, value: object) -> List[str]:
        """Parse CORS_ORIGINS from a comma-separated string into a list[str]."""
        if value is None or value == "":
            return ["http://localhost:3000"]
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        if isinstance(value, (list, tuple)):
            return [str(origin).strip() for origin in value if str(origin).strip()]
        raise TypeError(
            f"CORS_ORIGINS must be a comma-separated string or list, got {type(value).__name__}"
        )

    @property
    def max_file_size_bytes(self) -> int:
        """Maximum upload size expressed in bytes for use in size checks."""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024


@lru_cache(maxsize=1)
def _build_settings() -> Settings:
    """Construct and memoize the Settings singleton."""
    return Settings()


settings: Settings = _build_settings()


def get_settings() -> Settings:
    """Return the cached Settings instance.

    Designed to be used as a FastAPI dependency:
        from fastapi import Depends
        from app.config import Settings, get_settings

        @router.get("/example")
        async def example(cfg: Settings = Depends(get_settings)) -> dict:
            ...
    """
    return _build_settings()
