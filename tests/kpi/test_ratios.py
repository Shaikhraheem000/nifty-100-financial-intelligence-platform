import pytest
import math
from src.analytics.ratios import calculate_npm, calculate_opm, calculate_roe, calculate_roce

def test_npm():
    assert calculate_npm(10, 100) == 10.0
    assert calculate_npm(-5, 100) == -5.0
    assert calculate_npm(10, 0) is None
    assert calculate_npm(None, 100) is None

def test_opm():
    assert calculate_opm(20, 100) == 20.0
    assert calculate_opm(20, 0) is None

def test_roe_positive():
    # net_profit=100, equity=500 -> 20.0
    assert calculate_roe(100, 400, 100) == 20.0

def test_roe_neg_equity():
    # net_profit=100, equity=-50 -> None
    assert calculate_roe(100, -100, 50) is None
    assert calculate_roe(100, 0, 0) is None

def test_roce():
    # op_profit=50, dep=10 -> ebit=40
    # eq=100, res=50, bor=50 -> ce=200
    # 40 / 200 * 100 = 20.0
    assert calculate_roce(50, 10, 100, 50, 50) == 20.0
    
def test_roce_invalid_denominator():
    assert calculate_roce(50, 10, -50, -50, 0) is None
