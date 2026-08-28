import pytest
import math
from src.analytics.cagr import calculate_cagr

def test_cagr_normal():
    cagr, flag = calculate_cagr(100, 161.051, 5) # 100 * (1.1)^5 = 161.051
    assert math.isclose(cagr, 10.0, rel_tol=1e-3)
    assert flag is None

def test_cagr_turnaround():
    cagr, flag = calculate_cagr(-100, 200, 5)
    assert cagr is None
    assert flag == 'TURNAROUND'

def test_cagr_zero_base():
    cagr, flag = calculate_cagr(0, 100, 5)
    assert cagr is None
    assert flag == 'ZERO_BASE'

def test_cagr_both_negative():
    cagr, flag = calculate_cagr(-100, -50, 5)
    assert cagr is None
    assert flag == 'BOTH_NEGATIVE'

def test_cagr_decline_to_loss():
    cagr, flag = calculate_cagr(100, -50, 5)
    assert cagr is None
    assert flag == 'DECLINE_TO_LOSS'

def test_cagr_insufficient_history():
    cagr, flag = calculate_cagr(100, 200, 0)
    assert cagr is None
    assert flag == 'INSUFFICIENT'
