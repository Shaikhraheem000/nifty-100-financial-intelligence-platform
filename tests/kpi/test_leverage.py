import pytest
from src.analytics.leverage import calculate_de, calculate_icr, calculate_asset_turnover

def test_de_debtfree():
    # borrowings=0, equity=500 -> 0.0
    assert calculate_de(0, 400, 100) == 0.0

def test_de_invalid_equity():
    assert calculate_de(100, -50, 0) is None

def test_icr_debtfree():
    # interest=0 -> None
    assert calculate_icr(100, 10, 0) is None

def test_icr():
    assert calculate_icr(90, 10, 20) == 5.0

def test_asset_turnover():
    assert calculate_asset_turnover(100, 50) == 2.0
    assert calculate_asset_turnover(100, 0) is None
