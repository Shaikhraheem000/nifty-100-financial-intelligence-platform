import os
import pandas as pd
from src.screener.engine import ScreenerEngine

def write_screener_output(engine: ScreenerEngine, output_path: str):
    presets = ['quality', 'value', 'growth', 'dividend', 'debt_free', 'turnaround_watch']
    
    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # Formats
        green_fmt = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'})
        red_fmt = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
        
        for p in presets:
            df = engine.run_preset(p)
            sheet_name = p.capitalize()[:31]
            
            # Select 20 KPIs
            cols = ['company_name', 'broad_sector', 'composite_score', 'sector_rank', 'sector_percentile',
                    'return_on_equity_pct', 'debt_to_equity', 'free_cash_flow_cr', 'revenue_cagr_5yr',
                    'pat_cagr_5yr', 'pe_ratio', 'pb_ratio', 'dividend_yield_pct', 'interest_coverage',
                    'market_cap_crore', 'net_profit', 'eps_cagr_5yr', 'asset_turnover', 'sales']
            
            # Ensure all columns exist
            for c in cols:
                if c not in df.columns:
                    df[c] = None
                    
            df = df[cols]
            
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            worksheet = writer.sheets[sheet_name]
            
            # Simple conditional formatting (Example: top scores green)
            # For specific thresholds, we apply them here.
            # E.g., for composite score:
            worksheet.conditional_format('C2:C100', {'type': '3_color_scale'})
            
            filters = engine.config['presets'].get(p, {}) if p != 'turnaround_watch' else {}
            
            # Add basic formatting based on filters
            col_letters = {
                'return_on_equity_pct': 'F',
                'debt_to_equity': 'G',
                'pe_ratio': 'K',
                'pb_ratio': 'L'
            }
            
            if 'roe_min' in filters:
                worksheet.conditional_format(f"F2:F100", {'type': 'cell', 'criteria': '>=', 'value': filters['roe_min'], 'format': green_fmt})
                worksheet.conditional_format(f"F2:F100", {'type': 'cell', 'criteria': '<', 'value': filters['roe_min'], 'format': red_fmt})
                
            if 'de_max' in filters:
                worksheet.conditional_format(f"G2:G100", {'type': 'cell', 'criteria': '<=', 'value': filters['de_max'], 'format': green_fmt})
                worksheet.conditional_format(f"G2:G100", {'type': 'cell', 'criteria': '>', 'value': filters['de_max'], 'format': red_fmt})

if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    db_path = os.path.join(base_dir, 'data', 'nifty100.db')
    config_path = os.path.join(base_dir, 'config', 'screener_config.yaml')
    output_path = os.path.join(base_dir, 'output', 'screener_output.xlsx')
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    engine = ScreenerEngine(db_path, config_path)
    write_screener_output(engine, output_path)
    print("Screener generated.")
