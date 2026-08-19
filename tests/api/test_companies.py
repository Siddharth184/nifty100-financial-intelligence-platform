"""
API Integration tests for Companies endpoints — Sprint 6 Day 42.
"""

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_list_companies():
    response = client.get("/api/v1/companies")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 92
    assert len(data["companies"]) == 92


def test_list_companies_filter_sector():
    response = client.get("/api/v1/companies?sector=Information%20Technology")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] > 0


def test_get_company_profile_valid():
    response = client.get("/api/v1/companies/TCS")
    assert response.status_code == 200
    data = response.json()
    assert data["company_id"] == "TCS"
    assert "latest_kpis" in data


def test_get_company_profile_invalid_404():
    response = client.get("/api/v1/companies/INVALID_TICKER_XYZ")
    assert response.status_code == 404


def test_get_company_pl_history():
    response = client.get("/api/v1/companies/TCS/pl")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 5


def test_get_company_bs_history():
    response = client.get("/api/v1/companies/TCS/bs")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 5


def test_get_company_cashflow_history():
    response = client.get("/api/v1/companies/TCS/cashflow")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 5


def test_get_company_ratios_history():
    response = client.get("/api/v1/companies/TCS/ratios")
    assert response.status_code == 200
    data = response.json()
    assert data["years"] >= 5


def test_download_tearsheet_valid():
    response = client.get("/api/v1/companies/TCS/tearsheet")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


def test_download_tearsheet_skipped_company_404():
    # JIOFIN tearsheet was skipped legitimately (<3 years data)
    response = client.get("/api/v1/companies/JIOFIN/tearsheet")
    assert response.status_code == 404
