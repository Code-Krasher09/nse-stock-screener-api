"""
Integration tests for API routes.
"""
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from api.main import app


@pytest.mark.asyncio
async def test_health_check_route():
    """
    Test the health check endpoint.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code in [200, 207]
    assert response.json()["status"] in ["ok", "degraded"]
    assert "services" in response.json()


@pytest.mark.asyncio
@patch("api.routes.ingest.fetch_and_store_data")
async def test_ingest_trigger(mock_fetch):
    """
    Test the ingestion trigger endpoint.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/ingest/trigger")
    assert response.status_code == 202
    assert "started in the background" in response.json()["message"]


@pytest.mark.asyncio
async def test_screen_validation_error():
    """
    Test that invalid data passed to screener returns 422.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/screen", json={"price_min": "invalid"})
    assert response.status_code == 422

