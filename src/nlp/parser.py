import re
import os
import sqlite3
import pandas as pd

def parse_analysis_text(excel_path=None, db_path=None, output_dir=None):
    if output_dir is None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        output_dir = os.path.join(base_dir, 'output')
    os.makedirs(output_dir, exist_ok=True)

    if excel_path is None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        excel_path = os.path.join(base_dir, 'data', 'raw', 'analysis.xlsx')

    if db_path is None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        db_path = os.path.join(base_dir, 'data', 'nifty100.db')

    # Load raw analysis data
    # Header is on row 1 (0-indexed) in data/raw/analysis.xlsx
    df_raw = pd.read_excel(excel_path, header=1)

    target_fields = [
        'compounded_sales_growth',
        'compounded_profit_growth',
        'stock_price_cagr',
        'roe'
    ]

    pattern = re.compile(r'(\d+)\s*Years?:?\s*([\d.]+)%')

    parsed_records = []
    failure_records = []

    for _, row in df_raw.iterrows():
        cid = row.get('company_id')
        for metric in target_fields:
            val = row.get(metric)
            if pd.isna(val):
                continue
            text_str = str(val).strip()
            match = pattern.search(text_str)
            if match:
                period_years = int(match.group(1))
                value_pct = float(match.group(2))
                parsed_records.append({
                    'company_id': cid,
                    'metric_type': metric,
                    'period_years': period_years,
                    'value_pct': value_pct
                })
            else:
                reason = "Pattern mismatch"
                if "TTM" in text_str:
                    reason = "TTM period not in years"
                elif "Last Year" in text_str:
                    reason = "Last Year format without digit year"
                elif "-" in text_str:
                    reason = "Negative value not matched by positive regex"
                failure_records.append({
                    'company_id': cid,
                    'metric_type': metric,
                    'raw_text': text_str,
                    'reason': reason
                })

    parsed_df = pd.DataFrame(parsed_records)
    failures_df = pd.DataFrame(failure_records)

    parsed_out = os.path.join(output_dir, 'analysis_parsed.csv')
    failures_out = os.path.join(output_dir, 'parse_failures.csv')

    parsed_df.to_csv(parsed_out, index=False)
    failures_df.to_csv(failures_out, index=False)

    print(f"Parsed {len(parsed_df)} records saved to {parsed_out}")
    print(f"Logged {len(failures_df)} failures saved to {failures_out}")

    # Cross-validation against Ratio Engine
    divergences = []
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        ratios_df = pd.read_sql("SELECT company_id, year, revenue_cagr_5yr, pat_cagr_5yr FROM financial_ratios", conn)
        conn.close()

        # Get latest year ratio for each company
        ratios_df['year_str'] = ratios_df['year'].astype(str)
        latest_idx = ratios_df.groupby('company_id')['year_str'].idxmax()
        latest_ratios = ratios_df.loc[latest_idx].set_index('company_id')

        # Check 5-year sales growth
        sales_5yr = parsed_df[(parsed_df['metric_type'] == 'compounded_sales_growth') & (parsed_df['period_years'] == 5)]
        for _, r in sales_5yr.iterrows():
            cid = r['company_id']
            if cid in latest_ratios.index:
                computed_val = latest_ratios.loc[cid, 'revenue_cagr_5yr']
                if pd.notna(computed_val):
                    diff = abs(r['value_pct'] - computed_val)
                    if diff > 5.0:
                        divergences.append({
                            'company_id': cid,
                            'metric': 'sales_growth_5yr',
                            'parsed_val': r['value_pct'],
                            'computed_val': round(computed_val, 2),
                            'abs_diff': round(diff, 2),
                            'flag': 'Divergence > 5%'
                        })

        # Check 5-year profit growth
        profit_5yr = parsed_df[(parsed_df['metric_type'] == 'compounded_profit_growth') & (parsed_df['period_years'] == 5)]
        for _, r in profit_5yr.iterrows():
            cid = r['company_id']
            if cid in latest_ratios.index:
                computed_val = latest_ratios.loc[cid, 'pat_cagr_5yr']
                if pd.notna(computed_val):
                    diff = abs(r['value_pct'] - computed_val)
                    if diff > 5.0:
                        divergences.append({
                            'company_id': cid,
                            'metric': 'profit_growth_5yr',
                            'parsed_val': r['value_pct'],
                            'computed_val': round(computed_val, 2),
                            'abs_diff': round(diff, 2),
                            'flag': 'Divergence > 5%'
                        })

    divergence_df = pd.DataFrame(divergences)
    divergence_out = os.path.join(output_dir, 'cagr_divergence.csv')
    divergence_df.to_csv(divergence_out, index=False)
    print(f"Flagged {len(divergence_df)} CAGR divergences saved to {divergence_out}")

    return parsed_df, failures_df, divergence_df

if __name__ == '__main__':
    parse_analysis_text()
