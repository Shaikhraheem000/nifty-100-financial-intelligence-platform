import sqlite3
import pandas as pd
import os

def run_valuation(db_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    with sqlite3.connect(db_path) as conn:
        ratios = pd.read_sql("SELECT company_id, year, free_cash_flow_cr FROM financial_ratios", conn)
        mc = pd.read_sql("SELECT company_id, year as mc_year, pe_ratio, pb_ratio, ev_ebitda, market_cap_crore FROM market_cap", conn)
        sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
        companies = pd.read_sql("SELECT id as company_id, company_name FROM companies", conn)
        
    # Standardise year formatting to join
    ratios['year_str'] = ratios['year'].astype(str)
    ratios['year_prefix'] = ratios['year_str'].str[:4]
    mc['mc_year_str'] = mc['mc_year'].astype(str)
    
    df = ratios.merge(mc, left_on=['company_id', 'year_prefix'], right_on=['company_id', 'mc_year_str'], how='left')
    df = df.merge(sectors, on='company_id', how='left')
    df = df.merge(companies, on='company_id', how='left')
    
    # Latest Year Cross-section
    df['year_dt'] = pd.to_datetime(df['year_str'])
    idx = df.groupby('company_id')['year_dt'].idxmax()
    latest = df.loc[idx].copy()
    
    # 1. FCF Yield
    latest['FCF_yield_pct'] = (latest['free_cash_flow_cr'] / latest['market_cap_crore']) * 100
    
    # 2. 5yr Median P/E
    # We take the last 5 years per company
    df_sorted = df.sort_values(by=['company_id', 'year_dt'])
    last_5_years = df_sorted.groupby('company_id').tail(5)
    median_pe_5yr = last_5_years.groupby('company_id')['pe_ratio'].median().reset_index()
    median_pe_5yr.rename(columns={'pe_ratio': '5yr_median_PE'}, inplace=True)
    
    latest = latest.merge(median_pe_5yr, on='company_id', how='left')
    
    # 3. Sector Median P/E
    sector_medians = latest.groupby('broad_sector')['pe_ratio'].median().reset_index()
    sector_medians.rename(columns={'pe_ratio': 'sector_median_PE'}, inplace=True)
    
    latest = latest.merge(sector_medians, on='broad_sector', how='left')
    
    # 4. Overvaluation Flags
    def assign_flag(row):
        pe = row['pe_ratio']
        sec_med = row['sector_median_PE']
        if pd.isna(pe) or pd.isna(sec_med) or sec_med == 0:
            return 'Fair'
        if pe > sec_med * 1.5:
            return 'Caution'
        elif pe < sec_med * 0.7:
            return 'Discount'
        return 'Fair'
        
    latest['flag'] = latest.apply(assign_flag, axis=1)
    
    # PE vs Sector Median %
    latest['PE_vs_sector_median_pct'] = ((latest['pe_ratio'] - latest['sector_median_PE']) / latest['sector_median_PE']) * 100
    
    # Prepare Output
    output_cols = [
        'company_id', 'company_name', 'broad_sector', 
        'pe_ratio', 'pb_ratio', 'ev_ebitda', 
        'FCF_yield_pct', '5yr_median_PE', 'PE_vs_sector_median_pct', 'flag'
    ]
    
    # Rename broad_sector to sector
    latest.rename(columns={'broad_sector': 'sector'}, inplace=True)
    output_df = latest[['company_id', 'company_name', 'sector', 'pe_ratio', 'pb_ratio', 'ev_ebitda', 'FCF_yield_pct', '5yr_median_PE', 'PE_vs_sector_median_pct', 'flag']]
    
    # Save to Excel
    val_summary_path = os.path.join(output_dir, 'valuation_summary.xlsx')
    output_df.to_excel(val_summary_path, index=False)
    
    # Save Flags to CSV
    flags_df = output_df[output_df['flag'].isin(['Caution', 'Discount'])]
    val_flags_path = os.path.join(output_dir, 'valuation_flags.csv')
    flags_df.to_csv(val_flags_path, index=False)
    
    print(f"Valuation module complete. Processed {len(output_df)} companies.")

if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    db_path = os.path.join(base_dir, 'data', 'nifty100.db')
    output_dir = os.path.join(base_dir, 'output')
    
    run_valuation(db_path, output_dir)
