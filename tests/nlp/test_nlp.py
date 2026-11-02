import os
import re
import sqlite3
import pandas as pd
import pytest
from src.nlp.parser import parse_analysis_text
from src.nlp.pros_cons_generator import generate_pros_cons

def test_parser_regex():
    pattern = re.compile(r'(\d+)\s*Years?:?\s*([\d.]+)%')
    
    # Standard match
    match1 = pattern.search("10 Years: 21%")
    assert match1 is not None
    assert int(match1.group(1)) == 10
    assert float(match1.group(2)) == 21.0

    # Extra whitespace
    match2 = pattern.search("5 Years:       24%")
    assert match2 is not None
    assert int(match2.group(1)) == 5
    assert float(match2.group(2)) == 24.0

    # Non-matching TTM and Last Year
    assert pattern.search("TTM: 43%") is None
    assert pattern.search("Last Year: 12%") is None
    assert pattern.search("1 Year: -2%") is None

def test_parse_analysis_files():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    out_dir = os.path.join(base_dir, 'output')
    parsed_csv = os.path.join(out_dir, 'analysis_parsed.csv')
    failures_csv = os.path.join(out_dir, 'parse_failures.csv')

    assert os.path.exists(parsed_csv)
    assert os.path.exists(failures_csv)

    p_df = pd.read_csv(parsed_csv)
    f_df = pd.read_csv(failures_csv)

    assert len(p_df) > 0
    assert {'company_id', 'metric_type', 'period_years', 'value_pct'}.issubset(p_df.columns)
    assert len(f_df) > 0

def test_pros_cons_generated():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    out_file = os.path.join(base_dir, 'output', 'pros_cons_generated.csv')
    db_path = os.path.join(base_dir, 'data', 'nifty100.db')

    assert os.path.exists(out_file)
    df = pd.read_csv(out_file)

    # Required columns
    assert {'company_id', 'type', 'rule_id', 'text', 'confidence_pct'}.issubset(df.columns)

    # Confidence must be > 60%
    assert (df['confidence_pct'] > 60).all()

    # Every company must have >= 1 Pro and >= 1 Con
    conn = sqlite3.connect(db_path)
    all_companies = pd.read_sql('SELECT id FROM companies', conn)['id'].tolist()
    conn.close()

    pro_companies = set(df[df['type'] == 'pro']['company_id'])
    con_companies = set(df[df['type'] == 'con']['company_id'])

    for cid in all_companies:
        assert cid in pro_companies, f"Company {cid} missing Pro"
        assert cid in con_companies, f"Company {cid} missing Con"
