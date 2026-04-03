import pytest
from httpx import AsyncClient

@pytest.fixture
async def viewer_token(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "viewer@zorvyn.com", "password": "SecurePassword123!"}
    )
    return response.json()["access_token"]

@pytest.fixture
async def viewer_headers(viewer_token):
    return {"Authorization": f"Bearer {viewer_token}"}

@pytest.mark.asyncio
async def test_viewer_cannot_create_record(client: AsyncClient, viewer_headers: dict):
    response = await client.post(
        "/api/v1/records/",
        json={
            "amount": 500,
            "type": "income",
            "category": "Bonus",
            "date": "2026-04-01T00:00:00Z"
        },
        headers=viewer_headers
    )
    assert response.status_code == 403
    assert "not authorized" in response.json()["detail"]

@pytest.mark.asyncio
async def test_unauthenticated_gets_401(client: AsyncClient):
    response = await client.get("/api/v1/records/")
    assert response.status_code == 401
