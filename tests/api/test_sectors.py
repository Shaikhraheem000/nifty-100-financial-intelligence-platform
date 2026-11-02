"""
Unit tests for Sectors, Valuation, and Portfolio REST API endpoints.
"""

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_list_sectors():
    response = client.get("/api/v1/sectors")
    assert response.status_code == 200
    sectors = response.json()
    assert len(sectors) >= 10
    assert "sector" in sectors[0]
    assert "company_count" in sectors[0]
    assert "median_roe" in sectors[0]


def test_get_sector_companies_valid():
    response = client.get("/api/v1/sectors/Financials/companies")
    assert response.status_code == 200
    data = response.json()
    assert data["sector"] == "Financials"
    assert data["company_count"] > 0
    assert len(data["companies"]) > 0


def test_get_sector_companies_invalid_returns_404():
    response = client.get("/api/v1/sectors/UNKNOWN_SECTOR_XYZ/companies")
    assert response.status_code == 404


def test_get_valuation_multiples_tcs():
    response = client.get("/api/v1/market-cap/TCS")
    assert response.status_code == 200
    data = response.json()
    assert data["company_id"] == "TCS"
    assert data["history_count"] > 0
    assert "pe_ratio" in data["multiples"][0]


def test_get_portfolio_stats():
    response = client.get("/api/v1/portfolio/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["universe_size"] == 92
    assert data["metrics_count"] == 10
    assert len(data["statistics"]) == 10


def test_get_company_documents_tcs():
    response = client.get("/api/v1/companies/TCS/documents")
    assert response.status_code == 200
    data = response.json()
    assert data["company_id"] == "TCS"
    assert data["document_count"] > 0
    assert "is_url_valid" in data["documents"][0]
