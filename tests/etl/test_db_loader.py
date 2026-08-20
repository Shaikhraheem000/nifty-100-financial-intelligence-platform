import pytest
import os
from src.etl.db_loader import ETLPipeline

def test_db_loader_end_to_end():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    data_dir = os.path.join(base_dir, 'data')
    # Run with a temp DB to not overwrite the real one during tests
    db_path = os.path.join(data_dir, 'test_nifty100.db')
    
    pipeline = ETLPipeline(data_dir, db_path)
    pipeline.run()
    
    # Check that output db exists
    assert os.path.exists(db_path)
    
    import sqlite3
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        assert 'companies' in tables
        assert 'profitandloss' in tables
