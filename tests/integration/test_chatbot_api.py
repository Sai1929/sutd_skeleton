"""
Integration tests for the RAG chatbot API.
Requires a running system with ingested data.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_chatbot_requires_auth(client: AsyncClient):
    resp = await client.post("/api/v1/chatbot/query", json={"query": "test"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_chatbot_returns_response(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/api/v1/chatbot/query",
        json={"query": "What activities have been submitted?"},
        headers=auth_headers,
    )
    if resp.status_code == 503:
        pytest.skip("RAG chain not available in test environment")
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert "conversation_id" in data
    assert "sources" in data


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"student_id": "ADMIN001", "password": "Admin@123"},
    )
    if resp.status_code != 200:
        pytest.skip("Seeded DB not available")
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}
