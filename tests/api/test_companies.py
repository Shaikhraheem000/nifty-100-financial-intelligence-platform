"""
Unit and integration tests for Company REST API endpoints.
"""

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_get_companies_returns_92():
    response = client.get("/api/v1/companies")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 92
    assert "id" in data[0]
    assert "company_name" in data[0]
    assert "broad_sector" in data[0]


def test_get_companies_search_filter():
    response = client.get("/api/v1/companies?search=TCS")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(c["id"] == "TCS" for c in data)


def test_get_companies_sector_filter():
    response = client.get("/api/v1/companies?sector=Information Technology")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    for c in data:
        assert c["broad_sector"] == "Information Technology"


def test_get_single_company_valid_tcs():
    response = client.get("/api/v1/companies/TCS")
    assert response.status_code == 200
    profile = response.json()
    assert profile["id"] == "TCS"
    assert "Tata Consultancy Services" in profile["company_name"]
    assert profile["sector"] == "Information Technology"
    assert "latest_ratios" in profile


def test_get_single_company_invalid_returns_404():
    response = client.get("/api/v1/companies/INVALID_XYZ_TICKER")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_company_pl_history():
    response = client.get("/api/v1/companies/TCS/pl")
    assert response.status_code == 200
    pl_data = response.json()
    assert len(pl_data) >= 10
    assert "sales" in pl_data[0]
    assert "net_profit" in pl_data[0]


def test_get_company_bs_history():
    response = client.get("/api/v1/companies/TCS/bs")
    assert response.status_code == 200
    bs_data = response.json()
    assert len(bs_data) >= 10
    assert "borrowings" in bs_data[0]
    assert "total_assets" in bs_data[0]


def test_get_company_ratios_ten_plus_years():
    response = client.get("/api/v1/companies/TCS/ratios")
    assert response.status_code == 200
    ratios_data = response.json()
    assert len(ratios_data) >= 10
    assert "return_on_equity_pct" in ratios_data[0]


def test_get_company_tearsheet_pdf_download():
    response = client.get("/api/v1/companies/TCS/tearsheet")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert len(response.content) > 30000  # > 30 KB
