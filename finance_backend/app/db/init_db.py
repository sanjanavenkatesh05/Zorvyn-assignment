# =============================================================================
# Zorvyn Finance Backend — Database Initialization
# =============================================================================
# This module handles the asynchronous connection to MongoDB using Motor
# (async driver) and initializes Beanie ODM with all document models.
#
# Architecture:
#   Motor (async driver) → Beanie (ODM layer) → MongoDB
#
# The init_db() function is called once during application startup via
# FastAPI's lifespan context manager in main.py.
#
# Switching to MongoDB Atlas:
#   Simply change MONGO_URI in .env to your Atlas connection string:
#   MONGO_URI=mongodb+srv://<user>:<pass>@<cluster>.mongodb.net
#   No code changes required.
# =============================================================================

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.models import ALL_DOCUMENT_MODELS


# ---------------------------------------------------------------------------
# Module-level reference to the Motor client (for cleanup if needed)
# ---------------------------------------------------------------------------
_motor_client: AsyncIOMotorClient | None = None


async def init_db() -> None:
    """
    Initialize the MongoDB connection and Beanie ODM.

    This function:
    1. Creates an async Motor client connected to MONGO_URI.
    2. Selects the database specified by MONGO_DB_NAME.
    3. Initializes Beanie with all document models (User, Record).
       Beanie will automatically create collections and indexes.

    Called once during application startup. Do not call multiple times.

    Raises:
        ConnectionError: If MongoDB is unreachable (Motor will raise
                         on first actual operation, not on client creation).
    """
    global _motor_client

    print(f"📦 Connecting to MongoDB at: {settings.MONGO_URI}")
    print(f"📂 Using database: {settings.MONGO_DB_NAME}")

    # ── Step 1: Create the async Motor client ────────────────────────────
    # Motor's AsyncIOMotorClient is lazy — it doesn't actually connect
    # until the first database operation. This is by design for async apps.
    _motor_client = AsyncIOMotorClient(settings.MONGO_URI)

    # ── Step 2: Get the database reference ───────────────────────────────
    database = _motor_client[settings.MONGO_DB_NAME]

    # ── Step 3: Initialize Beanie ODM ────────────────────────────────────
    # This tells Beanie which database to use and which document models
    # to manage. Beanie will create collections and apply indexes.
    await init_beanie(
        database=database,
        document_models=ALL_DOCUMENT_MODELS,
    )

    print(f"✅ Beanie initialized with models: {[m.__name__ for m in ALL_DOCUMENT_MODELS]}")
    print("✅ Database connection established successfully!")
