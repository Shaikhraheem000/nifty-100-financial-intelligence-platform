"""
Unit tests for FastAPI health check and database telemetry endpoint.
"""

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_health_endpoint_status_200():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "uptime_seconds" in data
    assert "db_row_counts" in data


def test_health_endpoint_row_counts_all_10_tables():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    counts = response.json()["db_row_counts"]

    expected_tables = [
        "companies",
        "profitandloss",
        "balancesheet",
        "cashflow",
        "analysis",
        "documents",
        "prosandcons",
        "sectors",
        "stock_prices",
        "market_cap"
    ]

    for table in expected_tables:
        assert table in counts, f"Table {table} missing from health db_row_counts"
        assert counts[table] > 0, f"Table {table} has 0 rows"
    
    # Specifically verify companies table has 92 rows
    assert counts["companies"] == 92
