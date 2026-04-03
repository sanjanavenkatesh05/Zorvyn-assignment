import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_first_user_is_admin(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "admin@zorvyn.com",
            "password": "SecurePassword123!",
            "full_name": "Admin User"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "admin@zorvyn.com"
    assert data["role"] == "admin"

@pytest.mark.asyncio
async def test_register_second_user_is_viewer(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "viewer@zorvyn.com",
            "password": "SecurePassword123!",
            "full_name": "Viewer User"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "viewer@zorvyn.com"
    assert data["role"] == "viewer"

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "admin@zorvyn.com",
            "password": "SecurePassword123!"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "admin@zorvyn.com",
            "password": "WrongPassword!"
        }
    )
    assert response.status_code == 401
