"""
Unit tests for ETL normalisation functions (normalize_ticker and normalize_year).
Provides 20 unit tests for normalize_year covering all standard and edge-case variants.
"""

import pytest
from src.etl.normaliser import normalize_ticker, normalize_year


def test_ticker_normalise():
    assert normalize_ticker("TCS") == "TCS"
    assert normalize_ticker("  TCS  ") == "TCS"
    assert normalize_ticker("tcs") == "TCS"
    assert normalize_ticker("BAJAJ-AUTO") == "BAJAJ-AUTO"
    assert normalize_ticker("M&M") == "M&M"
    assert normalize_ticker("HDFCBANK") == "HDFCBANK"
    assert normalize_ticker(None) == "MISSING"
    assert normalize_ticker("") == "MISSING"


# 20 Distinct Unit Tests for normalize_year()
def test_norm_year_01_mar_dash_two_digits():
    assert normalize_year("Mar-23") == "2023-03"


def test_norm_year_02_mar_space_two_digits():
    assert normalize_year("Mar 23") == "2023-03"


def test_norm_year_03_march_dash_four_digits():
    assert normalize_year("March-2023") == "2023-03"


def test_norm_year_04_four_digits_standalone():
    assert normalize_year("2023") == "2023-03"


def test_norm_year_05_fy_prefix_two_digits():
    assert normalize_year("FY23") == "2023-03"


def test_norm_year_06_dec_dash_two_digits():
    assert normalize_year("Dec-22") == "2022-12"


def test_norm_year_07_standard_yyyy_mm():
    assert normalize_year("2023-03") == "2023-03"


def test_norm_year_08_jun_dash_two_digits():
    assert normalize_year("Jun-23") == "2023-06"


def test_norm_year_09_historical_mar_dash_12():
    assert normalize_year("Mar-12") == "2012-03"


def test_norm_year_10_historical_mar_space_12():
    assert normalize_year("Mar 12") == "2012-03"


def test_norm_year_11_historical_march_2012():
    assert normalize_year("March-2012") == "2012-03"


def test_norm_year_12_historical_2012():
    assert normalize_year("2012") == "2012-03"


def test_norm_year_13_historical_fy12():
    assert normalize_year("FY12") == "2012-03"


def test_norm_year_14_historical_dec_11():
    assert normalize_year("Dec-11") == "2011-12"


def test_norm_year_15_historical_standard_2012_03():
    assert normalize_year("2012-03") == "2012-03"


def test_norm_year_16_historical_jun_12():
    assert normalize_year("Jun-12") == "2012-06"


def test_norm_year_17_edge_garbage_string():
    assert normalize_year("garbage_text") == "PARSE_ERROR"


def test_norm_year_18_edge_fy_dash_invalid():
    assert normalize_year("FY-23") == "PARSE_ERROR"


def test_norm_year_19_edge_none_value():
    assert normalize_year(None) == "PARSE_ERROR"


def test_norm_year_20_edge_nan_float():
    assert normalize_year(float('nan')) == "PARSE_ERROR"
