"""
Unit tests for DataLoader (10 comprehensive tests).
Verifies loader reads correct structure, row counts, and column definitions across all datasets.
"""

import os
import pytest
import pandas as pd
from src.etl.loader import DataLoader

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_DIR = os.path.join(BASE_DIR, 'data')


@pytest.fixture
def loader():
    return DataLoader(DATA_DIR)


def test_01_loader_missing_file_raises_error():
    fake_loader = DataLoader("non_existent_directory_123")
    with pytest.raises(FileNotFoundError):
        fake_loader.load_dataset("companies")


def test_02_loader_companies_dataset(loader):
    df = loader.load_dataset("companies")
    assert not df.empty
    assert len(df) == 92
    assert "id" in df.columns or "company_id" in df.columns
    assert "company_name" in df.columns


def test_03_loader_profitandloss_dataset(loader):
    df = loader.load_dataset("profitandloss")
    assert not df.empty
    expected = {"sales", "operating_profit", "net_profit"}
    assert expected.issubset(set(df.columns))


def test_04_loader_balancesheet_dataset(loader):
    df = loader.load_dataset("balancesheet")
    assert not df.empty
    expected = {"borrowings", "total_assets", "total_liabilities"}
    assert expected.issubset(set(df.columns))


def test_05_loader_cashflow_dataset(loader):
    df = loader.load_dataset("cashflow")
    assert not df.empty
    expected = {"operating_activity", "investing_activity", "financing_activity"}
    assert expected.issubset(set(df.columns))


def test_06_loader_sectors_dataset(loader):
    df = loader.load_dataset("sectors")
    assert not df.empty
    assert "company_id" in df.columns
    assert "broad_sector" in df.columns


def test_07_loader_market_cap_dataset(loader):
    df = loader.load_dataset("market_cap")
    assert not df.empty
    assert "company_id" in df.columns
    assert "market_cap_crore" in df.columns


def test_08_loader_documents_dataset(loader):
    df = loader.load_dataset("documents")
    assert not df.empty
    assert "company_id" in df.columns
    assert "annual_report" in df.columns


def test_09_loader_manifest_generation(loader):
    loader.manifest = []
    df = loader.load_dataset("companies")
    assert len(loader.manifest) > 0
    m = loader.manifest[-1]
    assert m["dataset"] == "companies"
    assert m["row_count"] == len(df)
    assert "sha256" in m


def test_10_loader_analysis_dataset(loader):
    df = loader.load_dataset("analysis")
    assert not df.empty
    assert "company_id" in df.columns
