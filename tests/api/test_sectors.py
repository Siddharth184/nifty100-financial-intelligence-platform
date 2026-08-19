"""
API Integration tests for Sectors endpoints — Sprint 6 Day 42.
"""

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_list_sectors():
    response = client.get("/api/v1/sectors")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 10
    assert len(data["sectors"]) == 10


def test_get_sector_companies_valid():
    response = client.get("/api/v1/sectors/Information%20Technology/companies")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] > 0


def test_get_sector_companies_invalid_404():
    response = client.get("/api/v1/sectors/NonExistentSector/companies")
    assert response.status_code == 404
