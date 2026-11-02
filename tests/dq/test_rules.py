"""
Unit tests for Data Quality (DQ) validation rules (DQ-01 through DQ-16).
Crafts synthetic DataFrames triggering each specific rule and asserts rule_id and severity.
"""

import pytest
import pandas as pd
from src.etl.validator import Validator
from src.etl.deduplicator import Deduplicator


def test_dq_01_duplicate_company_pk():
    val = Validator()
    df = pd.DataFrame({"id": ["TCS", "TCS", "INFY"]})
    assert not val.validate_company_pk_uniqueness(df)
    rule_ids = [f["rule_id"] for f in val.failures]
    severities = [f["severity"] for f in val.failures]
    assert "DQ-01" in rule_ids
    assert "CRITICAL" in severities


def test_dq_02_duplicate_composite_key():
    dedup = Deduplicator()
    df = pd.DataFrame({
        "company_id": ["TCS", "TCS", "INFY"],
        "year": ["2023-03", "2023-03", "2023-03"],
        "val": [10, 20, 30]
    })
    res = dedup.deduplicate(df, ["company_id", "year"], "profitandloss")
    assert len(dedup.logs) > 0
    assert len(res) == 2


def test_dq_03_orphan_company_id():
    val = Validator()
    df = pd.DataFrame({"company_id": ["TCS", "ORPHAN_CORP"], "year": ["2023-03", "2023-03"]})
    master_ids = {"TCS", "INFY"}
    cleaned = val.validate_fk_integrity(df, master_ids, "profitandloss")
    rule_ids = [f["rule_id"] for f in val.failures]
    assert "DQ-03" in rule_ids
    assert len(cleaned) == 1


def test_dq_04_balance_sheet_mismatch():
    val = Validator()
    df = pd.DataFrame({
        "company_id": ["TCS"],
        "year": ["2023-03"],
        "total_assets": [100.0],
        "total_liabilities": [80.0],
        "fixed_assets": [20.0]
    })
    val.check_balance_sheet(df)
    rule_ids = [f["rule_id"] for f in val.failures]
    assert "DQ-04" in rule_ids


def test_dq_05_opm_mismatch():
    val = Validator()
    df = pd.DataFrame({
        "company_id": ["TCS"],
        "year": ["2023-03"],
        "sales": [100.0],
        "operating_profit": [20.0],
        "opm_percentage": [45.0],  # 20/100 = 20%, but opm is 45%
        "tax_percentage": [25.0],
        "dividend_payout": [30.0],
        "net_profit": [15.0],
        "eps": [5.0]
    })
    comp_df = pd.DataFrame({"id": ["TCS"]})
    val.check_profit_and_loss(df, comp_df)
    rule_ids = [f["rule_id"] for f in val.failures]
    assert "DQ-05" in rule_ids


def test_dq_06_non_positive_sales():
    val = Validator()
    df = pd.DataFrame({
        "company_id": ["TCS"],
        "year": ["2023-03"],
        "sales": [0.0],  # Non-positive sales
        "operating_profit": [0.0],
        "opm_percentage": [0.0],
        "tax_percentage": [25.0],
        "dividend_payout": [0.0],
        "net_profit": [-5.0],
        "eps": [-1.0]
    })
    comp_df = pd.DataFrame({"id": ["TCS"]})
    val.check_profit_and_loss(df, comp_df)
    rule_ids = [f["rule_id"] for f in val.failures]
    assert "DQ-06" in rule_ids


def test_dq_07_unparseable_year():
    val = Validator()
    df = pd.DataFrame({
        "company_id": ["TCS"],
        "year": ["INVALID_YEAR"]
    })
    val.check_year_format(df, "profitandloss")
    rule_ids = [f["rule_id"] for f in val.failures]
    assert "DQ-07" in rule_ids


def test_dq_08_invalid_ticker_format():
    val = Validator()
    df = pd.DataFrame({
        "company_id": ["A", "REALLY_REALLY_LONG_TICKER_NAME"],
        "year": ["2023-03", "2023-03"]
    })
    val.check_ticker_format(df, "profitandloss")
    rule_ids = [f["rule_id"] for f in val.failures]
    assert "DQ-08" in rule_ids


def test_dq_09_net_cash_flow_mismatch():
    val = Validator()
    df = pd.DataFrame({
        "company_id": ["TCS"],
        "year": ["2023-03"],
        "operating_activity": [100.0],
        "investing_activity": [-40.0],
        "financing_activity": [-30.0],
        "net_cash_flow": [999.0]  # Expected 30.0, diff = 969.0 > 10
    })
    val.check_cashflow(df)
    rule_ids = [f["rule_id"] for f in val.failures]
    assert "DQ-09" in rule_ids


def test_dq_10_negative_fixed_assets():
    val = Validator()
    df = pd.DataFrame({
        "company_id": ["TCS"],
        "year": ["2023-03"],
        "total_assets": [100.0],
        "total_liabilities": [100.0],
        "fixed_assets": [-15.0]  # Negative fixed assets
    })
    res = val.check_balance_sheet(df)
    rule_ids = [f["rule_id"] for f in val.failures]
    assert "DQ-10" in rule_ids
    assert res.iloc[0]["fixed_assets"] == 0  # Replaced with 0


def test_dq_11_tax_rate_out_of_range():
    val = Validator()
    df = pd.DataFrame({
        "company_id": ["TCS"],
        "year": ["2023-03"],
        "sales": [100.0],
        "operating_profit": [20.0],
        "opm_percentage": [20.0],
        "tax_percentage": [95.0],  # Out of range (>60)
        "dividend_payout": [20.0],
        "net_profit": [10.0],
        "eps": [2.0]
    })
    comp_df = pd.DataFrame({"id": ["TCS"]})
    val.check_profit_and_loss(df, comp_df)
    rule_ids = [f["rule_id"] for f in val.failures]
    assert "DQ-11" in rule_ids


def test_dq_12_dividend_payout_above_200():
    val = Validator()
    df = pd.DataFrame({
        "company_id": ["TCS"],
        "year": ["2023-03"],
        "sales": [100.0],
        "operating_profit": [20.0],
        "opm_percentage": [20.0],
        "tax_percentage": [25.0],
        "dividend_payout": [250.0],  # > 200%
        "net_profit": [10.0],
        "eps": [2.0]
    })
    comp_df = pd.DataFrame({"id": ["TCS"]})
    val.check_profit_and_loss(df, comp_df)
    rule_ids = [f["rule_id"] for f in val.failures]
    assert "DQ-12" in rule_ids


def test_dq_14_eps_sign_inconsistency():
    val = Validator()
    df = pd.DataFrame({
        "company_id": ["TCS"],
        "year": ["2023-03"],
        "sales": [100.0],
        "operating_profit": [20.0],
        "opm_percentage": [20.0],
        "tax_percentage": [25.0],
        "dividend_payout": [30.0],
        "net_profit": [50.0],  # Positive profit
        "eps": [-2.0]         # Inconsistent negative EPS
    })
    comp_df = pd.DataFrame({"id": ["TCS"]})
    val.check_profit_and_loss(df, comp_df)
    rule_ids = [f["rule_id"] for f in val.failures]
    assert "DQ-14" in rule_ids


def test_dq_16_coverage_less_than_five_years():
    val = Validator()
    df_pl = pd.DataFrame({
        "company_id": ["SHORT_CO", "SHORT_CO"],
        "year": ["2023-03", "2022-03"]  # Only 2 years
    })
    val.check_coverage(df_pl, pd.DataFrame(), pd.DataFrame())
    rule_ids = [f["rule_id"] for f in val.failures]
    assert "DQ-16" in rule_ids
