import sqlite3
import pandas as pd
import yaml
import os
from src.screener.scoring import calculate_composite_score
from src.screener.trend_filters import apply_turnaround_trend

class ScreenerEngine:
    def __init__(self, db_path: str, config_path: str):
        self.db_path = db_path
        self.config_path = config_path
        self.load_config()
        self.load_data()
        
    def load_config(self):
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
    def load_data(self):
        with sqlite3.connect(self.db_path) as conn:
            # We want the latest year per company for the main screener view
            # But we also need history for trend filters.
            self.ratios = pd.read_sql("SELECT * FROM financial_ratios", conn)
            
            # Additional raw fields might be needed like borrowings, dividend_yield
            mc = pd.read_sql("SELECT company_id, year, pe_ratio, pb_ratio, dividend_yield_pct, market_cap_crore FROM market_cap", conn)
            pl = pd.read_sql("SELECT company_id, year, sales, net_profit, dividend_payout FROM profitandloss", conn)
            bs = pd.read_sql("SELECT company_id, year, borrowings FROM balancesheet", conn)
            sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
            companies = pd.read_sql("SELECT id as company_id, company_name FROM companies", conn)
            
            self.ratios['year'] = self.ratios['year'].astype(str)
            self.ratios['year_prefix'] = self.ratios['year'].str[:4]
            mc['year'] = mc['year'].astype(str)
            pl['year'] = pl['year'].astype(str)
            bs['year'] = bs['year'].astype(str)
            
            # Merge
            df = self.ratios.merge(mc, left_on=['company_id', 'year_prefix'], right_on=['company_id', 'year'], how='left', suffixes=('', '_mc'))
            df = df.merge(pl, on=['company_id', 'year'], how='left')
            df = df.merge(bs, on=['company_id', 'year'], how='left')
            df = df.merge(sectors, on='company_id', how='left')
            df = df.merge(companies, on='company_id', how='left')
            
            df['year_dt'] = pd.to_datetime(df['year'])
            self.full_df = df.sort_values(by=['company_id', 'year_dt'])
            
            # Latest annual data for static screeners (prioritize rows with reported financial sales/P&L)
            if self.full_df['sales'].notna().any():
                idx = self.full_df[self.full_df['sales'].notna()].groupby('company_id')['year_dt'].idxmax()
            else:
                idx = self.full_df.groupby('company_id')['year_dt'].idxmax()
            self.latest_df = self.full_df.loc[idx].copy()
            
            # Score it
            self.latest_df = calculate_composite_score(self.latest_df)
            
    def apply_filters(self, df: pd.DataFrame, filters: dict) -> pd.DataFrame:
        res = df.copy()
        
        if 'roe_min' in filters:
            res = res[(res['return_on_equity_pct'] >= filters['roe_min']) | res['return_on_equity_pct'].isna()]
            # Wait, usually filters drop NaNs if they don't meet it. Let's drop NaN unless it's a special case.
            res = res[res['return_on_equity_pct'] >= filters['roe_min']]
            
        if 'de_max' in filters:
            # D/E max filter, but skip Financials
            cond = (res['debt_to_equity'] <= filters['de_max']) | (res['broad_sector'] == 'Financials') | (res['debt_to_equity'].isna() & (res['broad_sector'] == 'Financials'))
            res = res[cond]
            
        if 'fcf_min' in filters:
            res = res[res['free_cash_flow_cr'] >= filters['fcf_min']]
            
        if 'revenue_cagr_5yr_min' in filters:
            res = res[res['revenue_cagr_5yr'] >= filters['revenue_cagr_5yr_min']]
            
        if 'pat_cagr_5yr_min' in filters:
            res = res[res['pat_cagr_5yr'] >= filters['pat_cagr_5yr_min']]
            
        if 'pe_max' in filters:
            res = res[res['pe_ratio'] <= filters['pe_max']]
            
        if 'pb_max' in filters:
            res = res[res['pb_ratio'] <= filters['pb_max']]
            
        if 'dividend_yield_min' in filters:
            res = res[res['dividend_yield_pct'] >= filters['dividend_yield_min']]
            
        if 'dividend_payout_max' in filters:
            res = res[res['dividend_payout'] <= filters['dividend_payout_max']]
            
        if 'borrowings_max' in filters:
            res = res[res['borrowings'] <= filters['borrowings_max']]
            
        if 'sales_min' in filters:
            res = res[res['sales'] >= filters['sales_min']]
            
        if 'opm_min' in filters:
            res = res[res['operating_profit_margin_pct'] >= filters['opm_min']]
            
        if 'icr_min' in filters:
            # Debt free companies have interest_coverage = NaN, but borrowings = 0 or interest = 0
            # Let's say if interest_coverage is NaN and borrowings == 0, it passes
            cond = (res['interest_coverage'] >= filters['icr_min']) | (res['interest_coverage'].isna() & (res['borrowings'] == 0))
            res = res[cond]
            
        if 'market_cap_min' in filters:
            res = res[res['market_cap_crore'] >= filters['market_cap_min']]
            
        if 'net_profit_min' in filters:
            res = res[res['net_profit'] >= filters['net_profit_min']]
            
        if 'eps_cagr_min' in filters:
            res = res[res['eps_cagr_5yr'] >= filters['eps_cagr_min']]
            
        if 'asset_turnover_min' in filters:
            res = res[res['asset_turnover'] >= filters['asset_turnover_min']]
            
        # Add other custom filters here if called
        
        return res
        
    def run_preset(self, preset_name: str) -> pd.DataFrame:
        if preset_name == 'turnaround_watch':
            return apply_turnaround_trend(self.latest_df, self.full_df)
            
        filters = self.config['presets'].get(preset_name, {})
        
        # Debt-Free Blue Chip has some extra logic
        if preset_name == 'debt_free':
            # Add hardcoded blue-chip overrides from specification
            filters['roe_min'] = 12
            filters['sales_min'] = 5000
            filters['borrowings_max'] = 0
            
        if preset_name == 'dividend':
            filters['dividend_payout_max'] = 80
            filters['fcf_min'] = 0
            
        if preset_name == 'growth':
            filters['revenue_cagr_5yr_min'] = 15
            filters['de_max'] = 2.0
            
        if preset_name == 'value':
            filters['de_max'] = 2.0
            
        return self.apply_filters(self.latest_df, filters).sort_values('composite_score', ascending=False)
