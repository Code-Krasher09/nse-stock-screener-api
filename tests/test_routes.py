"""
Integration tests for API routes.
"""
import pytest
from httpx import AsyncClient
from api.main import app

@pytest.mark.asyncio
async def test_health_check_route():
    """
    Test the health check endpoint.
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_ingest_trigger():
    """
    Test the ingestion trigger endpoint.
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/ingest/trigger")
    assert response.status_code == 202
    assert "started in the background" in response.json()["message"]

@pytest.mark.asyncio
async def test_screen_validation_error():
    """
    Test that invalid data passed to screener returns 422.
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/screen", json={"price_min": "invalid"})
    assert response.status_code == 422
