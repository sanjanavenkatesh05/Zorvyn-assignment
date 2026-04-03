import pytest
from httpx import AsyncClient

@pytest.fixture
async def admin_token(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "admin@zorvyn.com", "password": "SecurePassword123!"}
    )
    return response.json()["access_token"]

@pytest.fixture
async def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}

@pytest.mark.asyncio
async def test_create_record(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/v1/records/",
        json={
            "amount": 500,
            "type": "income",
            "category": "Bonus",
            "date": "2026-04-01T00:00:00Z"
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == 500
    assert data["is_deleted"] == False

@pytest.mark.asyncio
async def test_get_records(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/records/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 1

@pytest.mark.asyncio
async def test_soft_delete_record(client: AsyncClient, auth_headers: dict):
    # Get a record to delete
    res = await client.get("/api/v1/records/", headers=auth_headers)
    record_id = res.json()["items"][0]["id"]

    # Delete it
    delete_res = await client.delete(f"/api/v1/records/{record_id}", headers=auth_headers)
    assert delete_res.status_code == 204

    # Try fetching normally (should missing)
    res_after = await client.get("/api/v1/records/", headers=auth_headers)
    assert not any(i["id"] == record_id for i in res_after.json()["items"])

    # Fetch with include_deleted=true
    res_incldel = await client.get("/api/v1/records/?include_deleted=true", headers=auth_headers)
    assert any(i["id"] == record_id for i in res_incldel.json()["items"])
