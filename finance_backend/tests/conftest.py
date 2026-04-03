import asyncio
import os
import pytest
from httpx import AsyncClient, ASGITransport
from motor.motor_asyncio import AsyncIOMotorClient

from app.main import app
from app.core.config import settings

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def client():
    """Test client and MongoDB test DB setup/teardown."""
    # Ensure test environment uses a specific test db
    os.environ["MONGO_DB_NAME"] = "zorvyn_finance_test"
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    # Cleanup the test database after the test session
    db_client: AsyncIOMotorClient = AsyncIOMotorClient(settings.MONGO_URI)
    await db_client.drop_database("zorvyn_finance_test")
