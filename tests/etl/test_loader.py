import pytest
import pandas as pd
from src.etl.loader import DataLoader
from src.etl.validator import Validator
from src.etl.deduplicator import Deduplicator
from src.etl.normaliser import normalize_ticker, normalize_year
import os

def test_loader_missing_file():
    loader = DataLoader("fake_dir")
    with pytest.raises(FileNotFoundError):
        loader.load_dataset("companies")

def test_validator_pk_uniqueness():
    val = Validator()
    df = pd.DataFrame({"id": ["TCS", "TCS", "INFY"]})
    assert not val.validate_company_pk_uniqueness(df)
    
    df2 = pd.DataFrame({"id": ["TCS", "INFY"]})
    assert val.validate_company_pk_uniqueness(df2)

def test_deduplicator():
    dedup = Deduplicator()
    df = pd.DataFrame({
        "company_id": ["TCS", "TCS", "INFY"],
        "year": ["2023", "2023", "2023"],
        "val": [1, 2, 3]
    })
    clean = dedup.deduplicate(df, ["company_id", "year"], "test")
    assert len(clean) == 2
    # Should keep last
    assert clean[clean["company_id"] == "TCS"]["val"].iloc[0] == 2

def test_fk_integrity():
    val = Validator()
    df = pd.DataFrame({"company_id": ["TCS", "MISSING_FK"]})
    master = {"TCS", "INFY"}
    clean = val.validate_fk_integrity(df, master, "test")
    assert len(clean) == 1
    assert clean.iloc[0]["company_id"] == "TCS"
    
def test_validator_check_balance_sheet():
    val = Validator()
    df = pd.DataFrame({
        "company_id": ["TCS", "INFY"],
        "year": ["2023", "2023"],
        "total_assets": [100, 100],
        "total_liabilities": [100, 50],
        "fixed_assets": [10, -5]
    })
    res = val.check_balance_sheet(df)
    assert res.iloc[1]["fixed_assets"] == 0
    assert len(val.failures) == 3 # 1 strict match, 1 mismatch, 1 negative FA

def test_validator_check_profit_and_loss():
    val = Validator()
    df = pd.DataFrame({
        "company_id": ["TCS", "INFY"],
        "year": ["2023", "2023"],
        "sales": [100, 0],
        "operating_profit": [20, -5],
        "opm_percentage": [20, 0],
        "tax_percentage": [25, 70],
        "dividend_payout": [50, 300],
        "net_profit": [10, 10],
        "eps": [5, -1]
    })
    comp_df = pd.DataFrame({"id": ["TCS", "INFY"]})
    val.check_profit_and_loss(df, comp_df)
    assert len(val.failures) >= 4

def test_validator_check_cashflow():
    val = Validator()
    df = pd.DataFrame({
        "company_id": ["TCS"],
        "year": ["2023"],
        "operating_activity": [10],
        "investing_activity": [10],
        "financing_activity": [10],
        "net_cash_flow": [100]
    })
    res = val.check_cashflow(df)
    assert res.iloc[0]["net_cash_flow"] == 30
    assert len(val.failures) == 1
