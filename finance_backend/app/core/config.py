# =============================================================================
# Zorvyn Finance Backend — Application Configuration
# =============================================================================
# This module centralizes all environment-based configuration using Pydantic
# Settings. Values are loaded from the .env file or environment variables.
#
# Usage:
#   from app.core.config import settings
#   print(settings.MONGO_URI)
# =============================================================================

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables / .env file.

    Attributes:
        MONGO_URI:           MongoDB connection string (local or Atlas).
        MONGO_DB_NAME:       Name of the MongoDB database to use.
        JWT_SECRET:          Secret key for signing JWT tokens.
        JWT_ALGORITHM:       Algorithm used for JWT encoding (default: HS256).
        JWT_EXPIRE_MINUTES:  Token expiration time in minutes (default: 60).
    """

    # ── MongoDB ──────────────────────────────────────────────────────────
    MONGO_URI: str = "mongodb://mongo:27017"
    MONGO_DB_NAME: str = "zorvyn_finance"

    # ── JWT Authentication ───────────────────────────────────────────────
    JWT_SECRET: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # Pydantic-settings configuration: read from .env file
    model_config = SettingsConfigDict(
        env_file=".env",       # Path to .env file (relative to working dir)
        env_file_encoding="utf-8",
        extra="ignore",        # Ignore extra env vars not defined here
    )


# ---------------------------------------------------------------------------
# Singleton instance — import this throughout the application
# ---------------------------------------------------------------------------
settings = Settings()
