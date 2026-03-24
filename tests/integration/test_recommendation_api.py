"""
Integration tests for the recommendation session API.
Requires a running Postgres + Redis (run setup_vm.sh first).
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_activities(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/v1/sessions/activities", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_start_session_requires_auth(client: AsyncClient):
    resp = await client.post("/api/v1/sessions/start", json={"activity_id": 1})
    assert resp.status_code == 401


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict:
    """Login and return auth headers. Requires seeded DB."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"student_id": "ADMIN001", "password": "Admin@123"},
    )
    if resp.status_code != 200:
        pytest.skip("Seeded DB not available — skipping integration test")
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
