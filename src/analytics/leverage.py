import pandas as pd

def calculate_de(borrowings: float, equity: float, reserves: float) -> float | None:
    if pd.isna(borrowings) or pd.isna(equity) or pd.isna(reserves):
        return None
        
    total_equity = equity + reserves
    if total_equity <= 0:
        return None
        
    return borrowings / total_equity

def calculate_icr(operating_profit: float, other_income: float, interest: float) -> float | None:
    if pd.isna(operating_profit) or pd.isna(interest):
        return None
        
    if interest == 0:
        return None # Debt Free handled by returning None and flagged later
        
    oi = other_income if pd.notna(other_income) else 0.0
    return (operating_profit + oi) / interest

def calculate_asset_turnover(sales: float, total_assets: float) -> float | None:
    if pd.isna(sales) or pd.isna(total_assets) or total_assets == 0:
        return None
        
    return sales / total_assets
