import os
import sqlite3
import pandas as pd
import numpy as np

def calculate_fcf(cfo: float, cfi: float) -> float | None:
    if pd.isna(cfo) or pd.isna(cfi):
        return None
    return cfo + cfi

def calculate_cfo_quality(cfo: float, pat: float) -> float | None:
    if pd.isna(cfo) or pd.isna(pat) or pat == 0:
        return None
    return cfo / pat

def calculate_capex_intensity(cfi: float, sales: float) -> float | None:
    if pd.isna(cfi) or pd.isna(sales) or sales == 0:
        return None
    return (abs(cfi) / sales) * 100.0

def calculate_fcf_conversion(fcf: float, op_profit: float) -> float | None:
    if pd.isna(fcf) or pd.isna(op_profit) or op_profit == 0:
        return None
    return (fcf / op_profit) * 100.0

def classify_capital_allocation(cfo: float, cfi: float, cff: float) -> str:
    """
    Returns pattern label based on signs:
    (+,-,-) Reinvestor / Debt Repayer
    (+,+,-) Asset Seller / Debt Repayer
    (+,-,+) Reinvestor / Raising Capital
    (+,+,+) Asset Seller / Raising Capital
    (-,-,-) Distress Burning Cash
    (-,+,-) Distress Asset Seller
    (-,-,+) Distress Raising Capital
    (-,+,+) Distress Raising Cap/Selling Assets
    """
    if pd.isna(cfo) or pd.isna(cfi) or pd.isna(cff):
        return "UNKNOWN"
        
    s_cfo = "+" if cfo >= 0 else "-"
    s_cfi = "+" if cfi >= 0 else "-"
    s_cff = "+" if cff >= 0 else "-"
    
    if s_cfo == "+" and s_cfi == "-" and s_cff == "-":
        return "Reinvestor / Debt Repayer"
    elif s_cfo == "+" and s_cfi == "+" and s_cff == "-":
        return "Asset Seller / Debt Repayer"
    elif s_cfo == "+" and s_cfi == "-" and s_cff == "+":
        return "Reinvestor / Raising Capital"
    elif s_cfo == "+" and s_cfi == "+" and s_cff == "+":
        return "Asset Seller / Raising Capital"
    elif s_cfo == "-" and s_cfi == "-" and s_cff == "-":
        return "Distress Burning Cash"
    elif s_cfo == "-" and s_cfi == "+" and s_cff == "-":
        return "Distress Asset Seller"
    elif s_cfo == "-" and s_cfi == "-" and s_cff == "+":
        return "Distress Raising Capital"
    elif s_cfo == "-" and s_cfi == "+" and s_cff == "+":
        return "Distress Raising Cap/Selling Assets"
        
    return "UNKNOWN"

def run_cashflow_intelligence(db_path=None, output_dir=None):
    if output_dir is None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        output_dir = os.path.join(base_dir, 'output')
    os.makedirs(output_dir, exist_ok=True)

    if db_path is None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        db_path = os.path.join(base_dir, 'data', 'nifty100.db')

    conn = sqlite3.connect(db_path)
    companies = pd.read_sql('SELECT id, company_name FROM companies', conn)
    cf = pd.read_sql('SELECT * FROM cashflow', conn)
    pl = pd.read_sql('SELECT * FROM profitandloss', conn)
    bs = pd.read_sql('SELECT * FROM balancesheet', conn)
    ratios = pd.read_sql('SELECT * FROM financial_ratios', conn)
    sectors = pd.read_sql('SELECT * FROM sectors', conn)
    conn.close()

    cf['year_dt'] = pd.to_datetime(cf['year'].astype(str))
    pl['year_dt'] = pd.to_datetime(pl['year'].astype(str))
    bs['year_dt'] = pd.to_datetime(bs['year'].astype(str))
    ratios['year_dt'] = pd.to_datetime(ratios['year'].astype(str))

    sectors_map = sectors.set_index('company_id')['broad_sector'].to_dict()

    cf_summary = []
    distress_alerts = []

    for cid in companies['id']:
        c_cf = cf[cf['company_id'] == cid].sort_values('year_dt')
        c_pl = pl[pl['company_id'] == cid].sort_values('year_dt')
        c_bs = bs[bs['company_id'] == cid].sort_values('year_dt')
        c_r = ratios[ratios['company_id'] == cid].sort_values('year_dt')
        sec = sectors_map.get(cid, 'Unknown')

        if c_cf.empty:
            cf_summary.append({
                'company_id': cid,
                'sector': sec,
                'cfo_quality_score': None,
                'cfo_quality_label': "Accrual Risk",
                'capex_intensity_pct': None,
                'capex_label': "Moderate",
                'fcf_cagr_5yr': None,
                'fcf_conversion_pct': None,
                'distress_flag': False,
                'deleveraging_flag': False,
                'capital_allocation_label': "UNKNOWN"
            })
            continue

        # Merge CF and PL for 5-year calculations
        # Standardise year prefix
        c_cf_copy = c_cf.copy()
        c_cf_copy['yp'] = c_cf_copy['year'].astype(str).str[:4]
        c_pl_copy = c_pl.copy()
        c_pl_copy['yp'] = c_pl_copy['year'].astype(str).str[:4]

        merged_hist = c_cf_copy.merge(c_pl_copy, on='yp', suffixes=('_cf', '_pl'))
        merged_hist = merged_hist.sort_values('year_dt_cf')

        # 1. CFO Quality Score: 5-year average of CFO / PAT
        last_5 = merged_hist.tail(5)
        cfo_pat_ratios = []
        for _, row in last_5.iterrows():
            cfo_val = row.get('operating_activity')
            pat_val = row.get('net_profit')
            q = calculate_cfo_quality(cfo_val, pat_val)
            if q is not None:
                cfo_pat_ratios.append(q)

        if len(cfo_pat_ratios) > 0:
            cfo_quality_score = float(np.mean(cfo_pat_ratios))
        else:
            cfo_quality_score = None

        if cfo_quality_score is not None:
            if cfo_quality_score > 1.0:
                cfo_quality_label = "High Quality"
            elif cfo_quality_score >= 0.5:
                cfo_quality_label = "Moderate"
            else:
                cfo_quality_label = "Accrual Risk"
        else:
            cfo_quality_label = "Accrual Risk"

        # 2. CapEx Intensity: abs(investing_activity) / sales * 100 for latest year
        lat_cf = c_cf.iloc[-1]
        lat_pl = c_pl.iloc[-1] if not c_pl.empty else None
        lat_bs = c_bs.iloc[-1] if not c_bs.empty else None
        lat_r = c_r.iloc[-1] if not c_r.empty else None

        cfi_val = lat_cf.get('investing_activity')
        sales_val = lat_pl.get('sales') if lat_pl is not None else None
        capex_intensity_pct = calculate_capex_intensity(cfi_val, sales_val)

        if capex_intensity_pct is not None:
            if capex_intensity_pct < 3.0:
                capex_label = "Asset Light"
            elif capex_intensity_pct <= 8.0:
                capex_label = "Moderate"
            else:
                capex_label = "Capital Intensive"
        else:
            capex_label = "Moderate"

        # 3. FCF CAGR 5yr and FCF Conversion
        fcf_conversion_pct = lat_r.get('fcf_conversion_pct') if lat_r is not None else None

        # Compute 5-year FCF CAGR
        # Using free_cash_flow_cr from ratios or (operating_activity + investing_activity)
        c_r_fcf = c_r.dropna(subset=['free_cash_flow_cr'])
        if len(c_r_fcf) >= 5:
            start_fcf = c_r_fcf.iloc[-5]['free_cash_flow_cr']
            end_fcf = c_r_fcf.iloc[-1]['free_cash_flow_cr']
            if start_fcf > 0 and end_fcf > 0:
                fcf_cagr_5yr = ((end_fcf / start_fcf) ** (1.0 / 5.0) - 1.0) * 100.0
            else:
                fcf_cagr_5yr = None
        else:
            fcf_cagr_5yr = None

        # 4. Distress Signal: CFO < 0 AND CFF > 0 in latest year
        cfo_lat = lat_cf.get('operating_activity', 0) or 0
        cff_lat = lat_cf.get('financing_activity', 0) or 0
        net_profit_lat = lat_pl.get('net_profit', 0) if lat_pl is not None else 0

        distress_flag = bool(cfo_lat < 0 and cff_lat > 0)
        if distress_flag:
            distress_alerts.append({
                'company_id': cid,
                'sector': sec,
                'cfo_crore': round(cfo_lat, 2),
                'cff_crore': round(cff_lat, 2),
                'latest_net_profit_crore': round(net_profit_lat, 2),
                'distress_reason': 'CFO < 0 and CFF > 0 (Operations burn cash while relying on financing)'
            })

        # 5. Deleveraging Flag: CFF < 0 AND borrowings declining year-over-year
        deleveraging_flag = False
        if len(c_bs) >= 2:
            prev_bs = c_bs.iloc[-2]
            prev_debt = prev_bs.get('borrowings', 0) or 0
            curr_debt = lat_bs.get('borrowings', 0) or 0
            if cff_lat < 0 and curr_debt < prev_debt:
                deleveraging_flag = True

        # 6. Capital Allocation Label for latest year
        cap_alloc_label = classify_capital_allocation(cfo_lat, cfi_val, cff_lat)

        cf_summary.append({
            'company_id': cid,
            'sector': sec,
            'cfo_quality_score': round(cfo_quality_score, 2) if cfo_quality_score is not None else None,
            'cfo_quality_label': cfo_quality_label,
            'capex_intensity_pct': round(capex_intensity_pct, 2) if capex_intensity_pct is not None else None,
            'capex_label': capex_label,
            'fcf_cagr_5yr': round(fcf_cagr_5yr, 2) if fcf_cagr_5yr is not None else None,
            'fcf_conversion_pct': round(fcf_conversion_pct, 2) if fcf_conversion_pct is not None else None,
            'distress_flag': distress_flag,
            'deleveraging_flag': deleveraging_flag,
            'capital_allocation_label': cap_alloc_label
        })

    summary_df = pd.DataFrame(cf_summary)
    excel_path = os.path.join(output_dir, 'cashflow_intelligence.xlsx')
    summary_df.to_excel(excel_path, index=False)
    print(f"Exported {len(summary_df)} rows to {excel_path}")

    alerts_df = pd.DataFrame(distress_alerts)
    alerts_path = os.path.join(output_dir, 'distress_alerts.csv')
    alerts_df.to_csv(alerts_path, index=False)
    print(f"Exported {len(alerts_df)} distress alerts to {alerts_path}")

    # Day 32: Pattern changes analysis from capital_allocation.csv
    cap_alloc_path = os.path.join(output_dir, 'capital_allocation.csv')
    if os.path.exists(cap_alloc_path):
        cap_df = pd.read_csv(cap_alloc_path)
        cap_df['year_dt'] = pd.to_datetime(cap_df['year'].astype(str))
        cap_df = cap_df.sort_values(['company_id', 'year_dt'])

        pattern_changes = []
        for cid, group in cap_df.groupby('company_id'):
            if len(group) >= 2:
                for i in range(1, len(group)):
                    prev_row = group.iloc[i - 1]
                    curr_row = group.iloc[i]
                    p_prev = prev_row['pattern_label']
                    p_curr = curr_row['pattern_label']
                    if p_prev != p_curr:
                        # Determine severity / transition nature
                        change_nature = "Neutral / Strategic"
                        if "Distress" in p_curr and "Distress" not in p_prev:
                            change_nature = "Deterioration to Distress"
                        elif "Distress" in p_prev and "Distress" not in p_curr:
                            change_nature = "Recovery from Distress"
                        elif "Debt Repayer" in p_curr:
                            change_nature = "Shift to Debt Repayment"
                        pattern_changes.append({
                            'company_id': cid,
                            'from_year': prev_row['year'],
                            'to_year': curr_row['year'],
                            'previous_pattern': p_prev,
                            'current_pattern': p_curr,
                            'transition_type': change_nature
                        })

        changes_df = pd.DataFrame(pattern_changes)
        changes_path = os.path.join(output_dir, 'pattern_changes.csv')
        changes_df.to_csv(changes_path, index=False)
        print(f"Exported {len(changes_df)} pattern transitions to {changes_path}")
    else:
        changes_df = pd.DataFrame()

    return summary_df, alerts_df, changes_df

if __name__ == '__main__':
    run_cashflow_intelligence()
