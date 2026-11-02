import pytest
import os
import sqlite3
import pandas as pd
from src.analytics.ratio_engine import RatioEngine

def test_ratio_engine_integration():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    db_path = os.path.join(base_dir, 'data', 'nifty100.db')
    output_dir = os.path.join(base_dir, 'output')
    
    engine = RatioEngine(db_path, output_dir)
    engine.run()
    
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql("SELECT * FROM financial_ratios", conn)
        
    assert len(df) > 1000
    
    # Check no duplicate company-year
    dups = df.duplicated(subset=['company_id', 'year'])
    assert not dups.any()
    
    assert 'net_profit_margin_pct' in df.columns
    assert 'return_on_equity_pct' in df.columns
    assert 'debt_to_equity' in df.columns
    
    # Check Idempotency by running it again
    engine.run()
    with sqlite3.connect(db_path) as conn:
        df2 = pd.read_sql("SELECT * FROM financial_ratios", conn)
        
    assert len(df) == len(df2)
