import pandas as pd

def apply_turnaround_trend(df: pd.DataFrame, base_df: pd.DataFrame) -> pd.DataFrame:
    """
    Turnaround Watch preset logic:
    - Revenue CAGR 3yr > 10%
    - FCF positive in latest year
    - D/E declining year-over-year
    
    `df` contains the latest cross-section (the latest year per company).
    `base_df` contains all historical data for checking D/E decline.
    """
    passed_companies = []
    
    for _, row in df.iterrows():
        c_id = row['company_id']
        year = row['year']
        
        # Rev CAGR 3yr > 10
        rev_cagr = row.get('revenue_cagr_3yr')
        if pd.isna(rev_cagr) or rev_cagr <= 10:
            continue
            
        # FCF positive in latest year
        fcf = row.get('free_cash_flow_cr')
        if pd.isna(fcf) or fcf <= 0:
            continue
            
        # D/E declining year-over-year
        company_hist = base_df[base_df['company_id'] == c_id].sort_values('year_dt')
        
        if len(company_hist) >= 2:
            latest_de = company_hist.iloc[-1]['debt_to_equity']
            prev_de = company_hist.iloc[-2]['debt_to_equity']
            
            # If both are valid and latest < prev, it's declining
            if pd.notna(latest_de) and pd.notna(prev_de) and latest_de < prev_de:
                passed_companies.append(c_id)
            elif latest_de == 0 and prev_de == 0:
                # Still debt free
                pass
    
    return df[df['company_id'].isin(passed_companies)].copy()
