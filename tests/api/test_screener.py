"""
Unit and functional tests for Screener REST API endpoint.
"""

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_screener_default():
    response = client.get("/api/v1/screener")
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert "results" in data
    assert data["count"] > 0


def test_screener_min_roe_filter():
    response = client.get("/api/v1/screener?min_roe=15")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] > 0
    for r in data["results"]:
        assert r["roe"] >= 15.0


def test_screener_invalid_parameter_returns_400():
    # Negative max_de
    response = client.get("/api/v1/screener?max_de=-0.5")
    assert response.status_code == 400
    assert "cannot be negative" in response.json()["detail"].lower()

    # Out of range min_roe
    response2 = client.get("/api/v1/screener?min_roe=-500")
    assert response2.status_code == 400


def test_screener_sector_filter():
    response = client.get("/api/v1/screener?sector=Financials")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] > 0
    for r in data["results"]:
        assert r["broad_sector"] == "Financials"
