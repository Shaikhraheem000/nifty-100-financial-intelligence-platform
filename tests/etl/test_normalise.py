import pytest
import pandas as pd
from src.etl.normaliser import normalize_ticker, normalize_year

def test_ticker_normalise():
    assert normalize_ticker("TCS") == "TCS"
    assert normalize_ticker("  TCS  ") == "TCS"
    assert normalize_ticker("tcs") == "TCS"
    assert normalize_ticker("  tcs  ") == "TCS"
    assert normalize_ticker("BAJAJ-AUTO") == "BAJAJ-AUTO"
    assert normalize_ticker("M&M") == "M&M"
    assert normalize_ticker("HDFCBANK") == "HDFCBANK"
    assert normalize_ticker("RELIANCE ") == "RELIANCE"
    assert normalize_ticker(" INFY") == "INFY"
    assert normalize_ticker("L&T") == "L&T"
    assert normalize_ticker("TATA-STEEL") == "TATA-STEEL"
    assert normalize_ticker(None) == "MISSING"
    assert normalize_ticker(float('nan')) == "MISSING"
    assert normalize_ticker("") == "MISSING"
    assert normalize_ticker("   ") == "MISSING"


def test_year_normalise():
    assert normalize_year("Mar-23") == "2023-03"
    assert normalize_year("Mar 23") == "2023-03"
    assert normalize_year("March-2023") == "2023-03"
    assert normalize_year("2023") == "2023-03"
    assert normalize_year("FY23") == "2023-03"
    assert normalize_year("Dec-22") == "2022-12"
    assert normalize_year("2023-03") == "2023-03"
    assert normalize_year("Jun-23") == "2023-06"
    
    assert normalize_year("Mar-12") == "2012-03"
    assert normalize_year("Mar 12") == "2012-03"
    assert normalize_year("March-2012") == "2012-03"
    assert normalize_year("2012") == "2012-03"
    assert normalize_year("FY12") == "2012-03"
    assert normalize_year("Dec-11") == "2011-12"
    assert normalize_year("2012-03") == "2012-03"
    assert normalize_year("Jun-12") == "2012-06"
    
    assert normalize_year("garbage") == "PARSE_ERROR"
    assert normalize_year("FY-23") == "PARSE_ERROR"
    assert normalize_year(None) == "PARSE_ERROR"
    assert normalize_year(float('nan')) == "PARSE_ERROR"
