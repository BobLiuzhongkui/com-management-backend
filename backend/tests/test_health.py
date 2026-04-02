"""
Tests for the health check endpoint.
"""
import pytest


@pytest.mark.asyncio
async def test_health_returns_ok(client):
    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "service" in body


@pytest.mark.asyncio
async def test_health_sets_no_auth_requirement(client):
    """Health endpoint must be publicly accessible."""
    response = await client.get("/health")
    assert response.status_code == 200
