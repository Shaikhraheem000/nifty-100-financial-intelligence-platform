import pandas as pd
import numpy as np

def calculate_npm(net_profit: float, sales: float) -> float | None:
    if pd.isna(net_profit) or pd.isna(sales) or sales == 0:
        return None
    return (net_profit / sales) * 100.0

def calculate_opm(operating_profit: float, sales: float) -> float | None:
    if pd.isna(operating_profit) or pd.isna(sales) or sales == 0:
        return None
    return (operating_profit / sales) * 100.0

def calculate_roe(net_profit: float, equity: float, reserves: float) -> float | None:
    if pd.isna(net_profit) or pd.isna(equity) or pd.isna(reserves):
        return None
    total_equity = equity + reserves
    if total_equity <= 0:
        return None
    return (net_profit / total_equity) * 100.0

def calculate_roce(operating_profit: float, depreciation: float, equity: float, reserves: float, borrowings: float) -> float | None:
    if pd.isna(operating_profit) or pd.isna(equity) or pd.isna(reserves) or pd.isna(borrowings):
        return None
        
    dep = depreciation if pd.notna(depreciation) else 0.0
    ebit = operating_profit - dep
    capital_employed = equity + reserves + borrowings
    
    if capital_employed <= 0:
        return None
    return (ebit / capital_employed) * 100.0
