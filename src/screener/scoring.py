import pandas as pd
import numpy as np

def winsorize_and_scale(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
    """Winsorizes at P10/P90 and scales to 0-100."""
    if len(series.dropna()) < 2:
        return pd.Series(50, index=series.index) # Default to 50 if not enough data
        
    p10 = series.quantile(0.10)
    p90 = series.quantile(0.90)
    
    # Cap values
    capped = series.clip(lower=p10, upper=p90)
    
    # Avoid division by zero
    if p90 == p10:
        return pd.Series(50, index=series.index)
        
    if higher_is_better:
        scaled = (capped - p10) / (p90 - p10) * 100
    else:
        scaled = (p90 - capped) / (p90 - p10) * 100
        
    return scaled

def calculate_composite_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates sector-relative composite score using:
    50% Profitability (ROE, ROCE, NPM)
    30% Growth (Revenue CAGR 5Y, PAT CAGR 5Y)
    20% Valuation (P/E, P/B)
    """
    df = df.copy()
    
    # Ensure columns exist, fill missing with sector median later
    cols = ['return_on_equity_pct', 'return_on_capital_pct', 'net_profit_margin_pct',
            'revenue_cagr_5yr', 'pat_cagr_5yr', 'pe_ratio', 'pb_ratio']
            
    for c in cols:
        if c not in df.columns:
            df[c] = np.nan
            
    scores = pd.DataFrame(index=df.index)
    
    # Group by sector for sector-relative normalization
    for sector, group in df.groupby('broad_sector'):
        idx = group.index
        
        # Profitability (Higher is better)
        roe_score = winsorize_and_scale(group['return_on_equity_pct'], True)
        roce_score = winsorize_and_scale(group['return_on_capital_pct'], True)
        npm_score = winsorize_and_scale(group['net_profit_margin_pct'], True)
        prof_score = roe_score.fillna(50) * 0.333 + roce_score.fillna(50) * 0.333 + npm_score.fillna(50) * 0.334
        
        # Growth (Higher is better)
        rev_cagr_score = winsorize_and_scale(group['revenue_cagr_5yr'], True)
        pat_cagr_score = winsorize_and_scale(group['pat_cagr_5yr'], True)
        growth_score = rev_cagr_score.fillna(50) * 0.5 + pat_cagr_score.fillna(50) * 0.5
        
        # Valuation (Lower is better)
        pe_score = winsorize_and_scale(group['pe_ratio'], False)
        pb_score = winsorize_and_scale(group['pb_ratio'], False)
        val_score = pe_score.fillna(50) * 0.5 + pb_score.fillna(50) * 0.5
        
        # Total
        comp_score = (prof_score * 0.50) + (growth_score * 0.30) + (val_score * 0.20)
        
        scores.loc[idx, 'composite_score'] = comp_score
        
    df['composite_score'] = scores['composite_score']
    
    # Calculate sector rank and percentile
    df['sector_rank'] = df.groupby('broad_sector')['composite_score'].rank(ascending=False, method='min')
    df['sector_percentile'] = df.groupby('broad_sector')['composite_score'].rank(pct=True) * 100
    
    return df
