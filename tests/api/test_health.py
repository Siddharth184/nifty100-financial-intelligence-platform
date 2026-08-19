"""
API Integration tests for Health endpoint — Sprint 6 Day 42.
"""

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_health_endpoint_200():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "db_row_counts" in data
    assert "uptime_seconds" in data
    assert data["db_row_counts"]["companies"] == 92
