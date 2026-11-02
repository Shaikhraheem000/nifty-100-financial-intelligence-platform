import pytest
import os
import sqlite3
import pandas as pd
from src.screener.engine import ScreenerEngine
from src.screener.scoring import winsorize_and_scale

def test_winsorize_and_scale():
    # Simple sequence 1 to 100
    s = pd.Series(range(1, 101))
    scaled = winsorize_and_scale(s, True)
    assert scaled.min() >= 0
    assert scaled.max() <= 100
    # Values <= 10th percentile should be 0, >= 90th percentile should be 100
    assert scaled.iloc[0] == 0.0
    assert scaled.iloc[99] == 100.0
    
def test_winsorize_and_scale_inverse():
    s = pd.Series(range(1, 101))
    scaled = winsorize_and_scale(s, False)
    assert scaled.iloc[0] == 100.0
    assert scaled.iloc[99] == 0.0

def test_screener_filters():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    db_path = os.path.join(base_dir, 'data', 'nifty100.db')
    config_path = os.path.join(base_dir, 'config', 'screener_config.yaml')
    
    engine = ScreenerEngine(db_path, config_path)
    
    df = engine.latest_df
    
    # Financials D/E carve-out test
    # Find a financials company that has D/E > 1
    # HDFC Bank has D/E ~ 7.39
    filters = {'de_max': 1.0}
    filtered = engine.apply_filters(df, filters)
    
    # Non-financials with D/E > 1 should be excluded
    non_fin_failed = df[(df['broad_sector'] != 'Financials') & (df['debt_to_equity'] > 1.0)]
    assert not any(filtered['company_id'].isin(non_fin_failed['company_id']))
    
    # Financials with D/E > 1 should be INCLUDED
    fin_passed = df[(df['broad_sector'] == 'Financials')]
    assert 'HDFCBANK' in filtered['company_id'].values or 'BAJFINANCE' in filtered['company_id'].values
    
def test_screener_presets():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    db_path = os.path.join(base_dir, 'data', 'nifty100.db')
    config_path = os.path.join(base_dir, 'config', 'screener_config.yaml')
    
    engine = ScreenerEngine(db_path, config_path)
    
    presets = ['quality', 'value', 'growth', 'dividend', 'debt_free', 'turnaround_watch']
    for p in presets:
        res = engine.run_preset(p)
        assert len(res) > 0, f"Preset {p} returned 0 results"
