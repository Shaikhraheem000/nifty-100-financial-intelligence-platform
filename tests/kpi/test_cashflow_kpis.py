import pytest
from src.analytics.cashflow_kpis import calculate_fcf, calculate_cfo_quality, calculate_capex_intensity, calculate_fcf_conversion, classify_capital_allocation

def test_cfo_pat():
    assert calculate_cfo_quality(100, 50) == 2.0
    assert calculate_cfo_quality(100, 0) is None

def test_fcf_conversion():
    assert calculate_fcf_conversion(50, 100) == 50.0
    assert calculate_fcf_conversion(50, 0) is None

def test_capital_allocation_patterns():
    assert classify_capital_allocation(10, -5, -5) == "Reinvestor / Debt Repayer"
    assert classify_capital_allocation(10, 5, -5) == "Asset Seller / Debt Repayer"
    assert classify_capital_allocation(10, -5, 5) == "Reinvestor / Raising Capital"
    assert classify_capital_allocation(10, 5, 5) == "Asset Seller / Raising Capital"
    assert classify_capital_allocation(-10, -5, -5) == "Distress Burning Cash"
    assert classify_capital_allocation(-10, 5, -5) == "Distress Asset Seller"
    assert classify_capital_allocation(-10, -5, 5) == "Distress Raising Capital"
    assert classify_capital_allocation(-10, 5, 5) == "Distress Raising Cap/Selling Assets"
    assert classify_capital_allocation(None, 5, 5) == "UNKNOWN"
