"""
Unit tests for financial ratios and KPI calculations (20 comprehensive unit tests).
Covers ROE, ROCE, NPM, OPM, D/E, ICR, Asset Turnover, CAGR flags, and CFO Quality.
"""

import pytest
from src.analytics.ratios import calculate_npm, calculate_opm, calculate_roe, calculate_roce
from src.analytics.leverage import calculate_de, calculate_icr, calculate_asset_turnover
from src.analytics.cagr import calculate_cagr
from src.analytics.cashflow_kpis import calculate_cfo_quality


def test_01_roe_positive_equity():
    assert calculate_roe(net_profit=100.0, equity=400.0, reserves=100.0) == 20.0


def test_02_roe_negative_equity_returns_none():
    assert calculate_roe(net_profit=100.0, equity=-150.0, reserves=50.0) is None


def test_03_roe_zero_equity_returns_none():
    assert calculate_roe(net_profit=50.0, equity=0.0, reserves=0.0) is None


def test_04_roe_missing_values_returns_none():
    assert calculate_roe(net_profit=None, equity=100.0, reserves=50.0) is None


def test_05_npm_normal_calculation():
    assert calculate_npm(net_profit=15.0, sales=100.0) == 15.0


def test_06_npm_loss_scenario():
    assert calculate_npm(net_profit=-10.0, sales=100.0) == -10.0


def test_07_opm_normal_calculation():
    assert calculate_opm(operating_profit=25.0, sales=100.0) == 25.0


def test_08_opm_zero_sales_returns_none():
    assert calculate_opm(operating_profit=20.0, sales=0.0) is None


def test_09_roce_normal_calculation():
    # ebit = 60 - 10 = 50. capital_employed = 100 + 100 + 50 = 250. 50/250 * 100 = 20.0
    assert calculate_roce(operating_profit=60.0, depreciation=10.0, equity=100.0, reserves=100.0, borrowings=50.0) == 20.0


def test_10_roce_invalid_negative_capital_employed():
    assert calculate_roce(operating_profit=50.0, depreciation=10.0, equity=-100.0, reserves=-100.0, borrowings=50.0) is None


def test_11_de_debt_free_company():
    # Borrowings = 0 -> D/E = 0.0
    assert calculate_de(borrowings=0.0, equity=500.0, reserves=500.0) == 0.0


def test_12_de_standard_calculation():
    assert calculate_de(borrowings=200.0, equity=50.0, reserves=50.0) == 2.0


def test_13_de_negative_equity_returns_none():
    assert calculate_de(borrowings=100.0, equity=-150.0, reserves=50.0) is None


def test_14_de_elevated_leverage_flag():
    de_val = calculate_de(borrowings=600.0, equity=50.0, reserves=50.0)
    assert de_val == 6.0
    # Flag elevated if > 5.0 for non-financial
    is_elevated_flag = de_val > 5.0
    assert is_elevated_flag is True


def test_15_icr_normal_calculation():
    # (OP + OI) / Interest = (100 + 20) / 10 = 12.0
    assert calculate_icr(operating_profit=100.0, other_income=20.0, interest=10.0) == 12.0


def test_16_icr_zero_interest_returns_none():
    # Zero interest indicates debt-free company
    assert calculate_icr(operating_profit=100.0, other_income=10.0, interest=0.0) is None


def test_17_asset_turnover_normal_and_zero_assets():
    assert calculate_asset_turnover(sales=200.0, total_assets=100.0) == 2.0
    assert calculate_asset_turnover(sales=200.0, total_assets=0.0) is None


def test_18_cagr_turnaround_flag():
    val, flag = calculate_cagr(start_val=-10.0, end_val=50.0, years=5)
    assert val is None
    assert flag == "TURNAROUND"


def test_19_cagr_decline_to_loss_flag():
    val, flag = calculate_cagr(start_val=50.0, end_val=-20.0, years=5)
    assert val is None
    assert flag == "DECLINE_TO_LOSS"


def test_20_cfo_quality_score_calculation():
    assert calculate_cfo_quality(cfo=150.0, pat=100.0) == 1.5
    assert calculate_cfo_quality(cfo=150.0, pat=0.0) is None
