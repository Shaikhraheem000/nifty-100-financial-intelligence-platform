import pandas as pd
import sqlite3
import logging
import os
from datetime import datetime
from src.analytics.ratios import calculate_npm, calculate_opm, calculate_roe, calculate_roce
from src.analytics.leverage import calculate_de, calculate_icr, calculate_asset_turnover
from src.analytics.cagr import calculate_cagr
from src.analytics.cashflow_kpis import calculate_fcf, calculate_cfo_quality, calculate_capex_intensity, calculate_fcf_conversion, classify_capital_allocation

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class RatioEngine:
    def __init__(self, db_path: str, output_dir: str):
        self.db_path = db_path
        self.output_dir = output_dir
        self.edge_cases_log = []
        self.sector_roce_notes = []
        
    def log_edge_case(self, company_id: str, year: str, metric: str, condition: str, input_values: str, result: float | None, flag: str) -> None:
        """Log calculation edge cases, substitutions, or anomalies."""
        self.edge_cases_log.append({
            'timestamp': datetime.now().isoformat(),
            'company_id': company_id,
            'year': year,
            'metric': metric,
            'condition': condition,
            'input_values': input_values,
            'result': result,
            'flag': flag
        })

    def run(self) -> None:
        """Execute full ratio computation engine across all available statement years."""
        start_time = datetime.now()
        
        with sqlite3.connect(self.db_path) as conn:
            pl_df = pd.read_sql("SELECT * FROM profitandloss", conn)
            bs_df = pd.read_sql("SELECT * FROM balancesheet", conn)
            cf_df = pd.read_sql("SELECT * FROM cashflow", conn)
            sectors_df = pd.read_sql("SELECT * FROM sectors", conn)
            companies_df = pd.read_sql("SELECT id, roce_percentage as src_roce, roe_percentage as src_roe FROM companies", conn)
            
        # Merge datasets using outer join to capture all available company-years across P&L, BS, and CF
        df = pl_df.merge(bs_df, on=['company_id', 'year'], how='outer')
        df = df.merge(cf_df, on=['company_id', 'year'], how='outer')
        df = df.merge(sectors_df[['company_id', 'broad_sector']], on='company_id', how='left')
        
        # Sort values chronologically
        df['year_dt'] = pd.to_datetime(df['year'])
        df = df.sort_values(by=['company_id', 'year_dt'])
        
        financial_ratios = []
        capital_allocation = []
        
        for idx, row in df.iterrows():
            c = row['company_id']
            y = row['year']
            sector = row.get('broad_sector', 'Unknown')
            
            # Profitability
            npm = calculate_npm(row.get('net_profit'), row.get('sales'))
            if row.get('sales') == 0:
                self.log_edge_case(c, y, 'NPM', 'sales=0', f"sales={row.get('sales')}", None, 'ZERO_SALES')
                
            opm = calculate_opm(row.get('operating_profit'), row.get('sales'))
            if pd.notna(opm) and pd.notna(row.get('opm_percentage')):
                src_opm = row.get('opm_percentage')
                if abs(opm - src_opm) > 1.0:
                    self.log_edge_case(c, y, 'OPM_CROSS_CHECK', 'difference > 1%', f"calc={opm}, src={src_opm}", opm, 'OPM_MISMATCH')
            
            roe = calculate_roe(row.get('net_profit'), row.get('equity_capital'), row.get('reserves'))
            eq = row.get('equity_capital', 0) + row.get('reserves', 0)
            if eq <= 0:
                self.log_edge_case(c, y, 'ROE', 'equity<=0', f"equity={eq}", None, 'NEGATIVE_EQUITY')
                
            roce = calculate_roce(row.get('operating_profit'), row.get('depreciation'), row.get('equity_capital'), row.get('reserves'), row.get('borrowings'))
            
            # ROCE cross-check and Bank/NBFC
            is_financial = sector == 'Financials'
            # Note: The project spec says apply sector-relative methodology. For now we calculate it and log differences.
            src_roce = companies_df[companies_df['id'] == c]['src_roce'].iloc[0] if not companies_df[companies_df['id'] == c].empty else None
            if pd.notna(roce) and pd.notna(src_roce) and is_financial:
                diff = abs(roce - src_roce)
                if diff > 1.0:
                    self.sector_roce_notes.append({
                        'company_id': c, 'sector': sector, 'year': y, 
                        'computed_roce': roce, 'source_roce': src_roce, 
                        'difference': diff, 'difference_pct': diff / src_roce if src_roce != 0 else 0,
                        'status': 'ANOMALY'
                    })
                    self.log_edge_case(c, y, 'ROCE_FINANCIAL', 'difference vs source', f"calc={roce}, src={src_roce}", roce, 'ROCE_ANOMALY')
            
            # Leverage & Efficiency
            de = calculate_de(row.get('borrowings'), row.get('equity_capital'), row.get('reserves'))
            if eq <= 0:
                self.log_edge_case(c, y, 'D/E', 'equity<=0', f"equity={eq}", None, 'NEGATIVE_EQUITY')
            if pd.notna(de) and de == 0:
                self.log_edge_case(c, y, 'D/E', 'debt-free', f"borrowings=0", de, 'DEBT_FREE')
            if pd.notna(de) and de > 5 and not is_financial:
                self.log_edge_case(c, y, 'D/E', 'de>5 non-financial', f"de={de}", de, 'HIGH_DE')
                
            icr = calculate_icr(row.get('operating_profit'), row.get('other_income'), row.get('interest'))
            if row.get('interest') == 0:
                self.log_edge_case(c, y, 'ICR', 'interest=0', "interest=0", None, 'DEBT_FREE')
                
            at = calculate_asset_turnover(row.get('sales'), row.get('total_assets'))
            if row.get('total_assets') == 0:
                self.log_edge_case(c, y, 'Asset Turnover', 'total_assets=0', "assets=0", None, 'ZERO_ASSETS')
                
            # Cash Flow
            fcf = calculate_fcf(row.get('operating_activity'), row.get('investing_activity'))
            cfo_q = calculate_cfo_quality(row.get('operating_activity'), row.get('net_profit'))
            if row.get('net_profit') == 0:
                self.log_edge_case(c, y, 'CFO Quality', 'pat=0', "pat=0", None, 'ZERO_PAT')
                
            capex_int = calculate_capex_intensity(row.get('investing_activity'), row.get('sales'))
            fcf_conv = calculate_fcf_conversion(fcf, row.get('operating_profit'))
            
            cfo = row.get('operating_activity')
            cfi = row.get('investing_activity')
            cff = row.get('financing_activity')
            pattern = classify_capital_allocation(cfo, cfi, cff)
            
            capital_allocation.append({
                'company_id': c, 'year': y, 
                'CFO_sign': '+' if pd.notna(cfo) and cfo>=0 else '-',
                'CFI_sign': '+' if pd.notna(cfi) and cfi>=0 else '-',
                'CFF_sign': '+' if pd.notna(cff) and cff>=0 else '-',
                'pattern_label': pattern
            })
            
            # Growth metrics (CAGR)
            # Need historical data, fetch from the dataframe subset for this company up to this year
            hist_df = df[(df['company_id'] == c) & (df['year_dt'] <= row['year_dt'])].sort_values(by='year_dt')
            cagrs = {}
            for metric in ['sales', 'net_profit', 'eps']:
                for window in [3, 5, 10]:
                    key = f"{metric}_cagr_{window}yr"
                    if len(hist_df) > window:
                        end_val = row.get(metric)
                        start_val = hist_df.iloc[-(window+1)].get(metric)
                        val, flag = calculate_cagr(start_val, end_val, window)
                        if flag:
                            self.log_edge_case(c, y, key, flag, f"start={start_val}, end={end_val}", None, flag)
                        cagrs[key] = val
                    else:
                        cagrs[key] = None
            
            financial_ratios.append({
                'company_id': c,
                'year': y,
                'net_profit_margin_pct': npm,
                'operating_profit_margin_pct': opm,
                'return_on_equity_pct': roe,
                'return_on_capital_pct': roce,
                'debt_to_equity': de,
                'interest_coverage': icr,
                'asset_turnover': at,
                'free_cash_flow_cr': fcf,
                'cfo_quality_ratio': cfo_q,
                'capex_intensity_pct': capex_int,
                'fcf_conversion_pct': fcf_conv,
                'revenue_cagr_3yr': cagrs.get('sales_cagr_3yr'),
                'revenue_cagr_5yr': cagrs.get('sales_cagr_5yr'),
                'revenue_cagr_10yr': cagrs.get('sales_cagr_10yr'),
                'pat_cagr_3yr': cagrs.get('net_profit_cagr_3yr'),
                'pat_cagr_5yr': cagrs.get('net_profit_cagr_5yr'),
                'pat_cagr_10yr': cagrs.get('net_profit_cagr_10yr'),
                'eps_cagr_3yr': cagrs.get('eps_cagr_3yr'),
                'eps_cagr_5yr': cagrs.get('eps_cagr_5yr'),
                'eps_cagr_10yr': cagrs.get('eps_cagr_10yr')
            })
            
        # Write DB
        ratios_df = pd.DataFrame(financial_ratios)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            # Remove old data to be idempotent
            conn.execute("DELETE FROM financial_ratios;")
            ratios_df.to_sql('financial_ratios', conn, if_exists='append', index=False)
                
        # Write outputs
        os.makedirs(self.output_dir, exist_ok=True)
        docs_dir = os.path.join(self.output_dir, '..', 'docs')
        os.makedirs(docs_dir, exist_ok=True)
        
        pd.DataFrame(self.edge_cases_log).to_csv(os.path.join(docs_dir, 'ratio_edge_cases.log'), index=False)
        pd.DataFrame(capital_allocation).to_csv(os.path.join(self.output_dir, 'capital_allocation.csv'), index=False)
        if self.sector_roce_notes:
            pd.DataFrame(self.sector_roce_notes).to_csv(os.path.join(docs_dir, 'sector_roce_notes.csv'), index=False)
            
        runtime = (datetime.now() - start_time).total_seconds()
        logger.info(f"Ratio Engine complete. Processed {len(ratios_df)} KPI rows in {runtime:.2f}s")
        
if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    db_path = os.path.join(base_dir, 'data', 'nifty100.db')
    output_dir = os.path.join(base_dir, 'output')
    
    engine = RatioEngine(db_path, output_dir)
    engine.run()
