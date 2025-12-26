"""Tests for health check endpoint"""

import pytest
from httpx import ASGITransport, AsyncClient

from voice_assistant.main import app


@pytest.fixture
async def client():
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_check_returns_ok(client: AsyncClient):
    """Test that health check endpoint returns status ok."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_health_check_content_type(client: AsyncClient):
    """Test that health check returns JSON content type."""
    response = await client.get("/api/v1/health")
    assert "application/json" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_health_check_method_not_allowed(client: AsyncClient):
    """Test that POST to health check returns 405 Method Not Allowed."""
    response = await client.post("/api/v1/health")
    assert response.status_code == 405


@pytest.mark.asyncio
async def test_nonexistent_endpoint_returns_404(client: AsyncClient):
    """Test that non-existent endpoint returns 404."""
    response = await client.get("/api/v1/nonexistent")
    assert response.status_code == 404
