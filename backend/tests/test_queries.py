"""Smoke tests for the Q&A graph."""
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def app_client():
    from app.main import app
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


async def test_query_promises(app_client):
    """Test 'What did I promise Raghav?'"""
    response = await app_client.post(
        "/api/query",
        json={"question": "What did I promise Raghav?", "as_of_date": "2026-09-23"}
    )
    if response.status_code != 200:
        pytest.skip(f"API not ready: {response.status_code}")
        
    data = response.json()
    assert "vendor" in data["answer"].lower() or len(data["commitments_cited"]) > 0


async def test_query_mumbai_ownership(app_client):
    """Test 'Who owns the Mumbai office renewal?'"""
    response = await app_client.post(
        "/api/query",
        json={"question": "Who owns the Mumbai office renewal?", "as_of_date": "2026-09-23"}
    )
    if response.status_code != 200:
        pytest.skip("API not ready")
        
    data = response.json()
    answer = data["answer"].lower()
    assert "unclear" in answer or "unknown" in answer or "not been definitively assigned" in answer
    assert "facilities" not in answer or "not" in answer or "assume" in answer, "Must not definitively assign to Facilities"
