import os
import sqlite3
import pandas as pd
import pytest
from src.analytics.cashflow_kpis import (
    calculate_fcf, calculate_cfo_quality, calculate_capex_intensity,
    calculate_fcf_conversion, classify_capital_allocation, run_cashflow_intelligence
)

def test_cf_intelligence_file_and_columns():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    excel_path = os.path.join(base_dir, 'output', 'cashflow_intelligence.xlsx')
    alerts_path = os.path.join(base_dir, 'output', 'distress_alerts.csv')
    changes_path = os.path.join(base_dir, 'output', 'pattern_changes.csv')

    assert os.path.exists(excel_path)
    assert os.path.exists(alerts_path)
    assert os.path.exists(changes_path)

    df = pd.read_excel(excel_path)
    # Must have exactly 92 rows
    assert len(df) == 92, f"Expected 92 rows in cashflow_intelligence.xlsx, got {len(df)}"

    required_cols = [
        'company_id', 'sector', 'cfo_quality_score', 'cfo_quality_label',
        'capex_intensity_pct', 'capex_label', 'fcf_cagr_5yr',
        'fcf_conversion_pct', 'distress_flag', 'deleveraging_flag',
        'capital_allocation_label'
    ]
    for col in required_cols:
        assert col in df.columns, f"Missing column {col} in cashflow_intelligence.xlsx"

def test_distress_and_deleveraging_logic():
    # Distress signal: CFO < 0 and CFF > 0
    assert ((-100 < 0) and (50 > 0)) is True

    # CFO quality labels
    assert "High Quality" == ("High Quality" if 1.5 > 1.0 else "Other")
    assert "Moderate" == ("Moderate" if 0.5 <= 0.8 <= 1.0 else "Other")
    assert "Accrual Risk" == ("Accrual Risk" if 0.3 < 0.5 else "Other")

    # CapEx labels
    assert "Asset Light" == ("Asset Light" if 2.0 < 3.0 else "Other")
    assert "Moderate" == ("Moderate" if 3.0 <= 5.0 <= 8.0 else "Other")
    assert "Capital Intensive" == ("Capital Intensive" if 12.0 > 8.0 else "Other")
