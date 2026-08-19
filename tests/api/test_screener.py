"""
API Integration tests for Screener endpoint — Sprint 6 Day 42.
"""

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_screener_default():
    response = client.get("/api/v1/screener")
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert data["count"] > 0


def test_screener_preset_quality_compounder():
    response = client.get("/api/v1/screener?preset=quality_compounder")
    assert response.status_code == 200
    data = response.json()
    assert data["preset"] == "quality_compounder"
    assert "companies" in data


def test_screener_invalid_preset_400():
    response = client.get("/api/v1/screener?preset=invalid_preset_name")
    assert response.status_code == 400


def test_screener_custom_filters():
    response = client.get("/api/v1/screener?roe_min=15.0&de_max=1.0")
    assert response.status_code == 200
    data = response.json()
    assert data["filters_applied"]["roe_min"] == 15.0
    assert data["filters_applied"]["de_max"] == 1.0
