import pandas as pd
from typing import Tuple

def calculate_cagr(start_val: float, end_val: float, years: int) -> Tuple[float | None, str | None]:
    """
    Returns (cagr_percentage, flag)
    """
    if pd.isna(start_val) or pd.isna(end_val) or years <= 0:
        return None, "INSUFFICIENT"
        
    if start_val == 0:
        return None, "ZERO_BASE"
        
    if start_val < 0 and end_val > 0:
        return None, "TURNAROUND"
        
    if start_val < 0 and end_val < 0:
        return None, "BOTH_NEGATIVE"
        
    if start_val > 0 and end_val < 0:
        return None, "DECLINE_TO_LOSS"
        
    cagr = ((end_val / start_val) ** (1 / years)) - 1
    return cagr * 100.0, None
