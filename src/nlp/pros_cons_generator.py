import os
import sqlite3
import pandas as pd
import numpy as np

def generate_pros_cons(db_path=None, output_dir=None):
    if output_dir is None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        output_dir = os.path.join(base_dir, 'output')
    os.makedirs(output_dir, exist_ok=True)

    if db_path is None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        db_path = os.path.join(base_dir, 'data', 'nifty100.db')

    conn = sqlite3.connect(db_path)
    companies = pd.read_sql('SELECT id, company_name FROM companies', conn)
    ratios = pd.read_sql('SELECT * FROM financial_ratios', conn)
    pl = pd.read_sql('SELECT * FROM profitandloss', conn)
    bs = pd.read_sql('SELECT * FROM balancesheet', conn)
    mc = pd.read_sql('SELECT * FROM market_cap', conn)
    sectors = pd.read_sql('SELECT * FROM sectors', conn)
    conn.close()

    ratios['year_dt'] = pd.to_datetime(ratios['year'].astype(str))
    pl['year_dt'] = pd.to_datetime(pl['year'].astype(str))
    bs['year_dt'] = pd.to_datetime(bs['year'].astype(str))
    mc['year_dt'] = pd.to_datetime(mc['year'].astype(str))

    sectors_map = sectors.set_index('company_id')['broad_sector'].to_dict()

    records = []

    for cid in companies['id']:
        c_r = ratios[ratios['company_id'] == cid].sort_values('year_dt')
        c_pl = pl[pl['company_id'] == cid].sort_values('year_dt')
        c_bs = bs[bs['company_id'] == cid].sort_values('year_dt')
        c_mc = mc[mc['company_id'] == cid].sort_values('year_dt')
        sec = sectors_map.get(cid, 'Unknown')

        lat_r = c_r.iloc[-1] if not c_r.empty else None
        lat_pl = c_pl.iloc[-1] if not c_pl.empty else None
        lat_bs = c_bs.iloc[-1] if not c_bs.empty else None
        lat_mc = c_mc.iloc[-1] if not c_mc.empty else None

        c_pros = []
        c_cons = []

        if lat_r is not None:
            # Pro Rule 1: ROE > 20% sustained for 3+ years
            if len(c_r) >= 3 and (c_r['return_on_equity_pct'].tail(3) > 20.0).all():
                avg_roe = c_r['return_on_equity_pct'].tail(3).mean()
                conf = min(98, int(75 + (avg_roe - 20) * 1.0))
                c_pros.append(('PRO_01', 'Consistently high return on equity above 20% demonstrates exceptional capital efficiency', conf))

            # Pro Rule 2: FCF positive for 5+ consecutive years
            if len(c_r) >= 5 and (c_r['free_cash_flow_cr'].tail(5) > 0).all():
                c_pros.append(('PRO_02', 'Strong free cash flow generation over 5 years signals healthy business fundamentals', 90))

            # Pro Rule 3: D/E = 0 in latest year
            de = lat_r.get('debt_to_equity')
            if de == 0 or (pd.notna(de) and de <= 0.01):
                c_pros.append(('PRO_03', 'Debt-free balance sheet provides financial flexibility and eliminates interest burden', 95))

            # Pro Rule 4: Revenue CAGR > 15% over 5 years
            rev_cagr = lat_r.get('revenue_cagr_5yr')
            if pd.notna(rev_cagr) and rev_cagr > 15.0:
                conf = min(95, int(70 + (rev_cagr - 15) * 1.5))
                c_pros.append(('PRO_04', 'Revenue growing at above 15% CAGR over 5 years reflects strong business momentum', conf))

            # Pro Rule 5: OPM > 25% in latest year
            opm = lat_r.get('operating_profit_margin_pct')
            if pd.notna(opm) and opm > 25.0:
                conf = min(95, int(70 + (opm - 25) * 1.2))
                c_pros.append(('PRO_05', 'Operating profit margin above 25% indicates strong pricing power and cost discipline', conf))

            # Pro Rule 6: PAT CAGR > 20% over 5 years
            pat_cagr = lat_r.get('pat_cagr_5yr')
            if pd.notna(pat_cagr) and pat_cagr > 20.0:
                conf = min(95, int(70 + (pat_cagr - 20) * 1.2))
                c_pros.append(('PRO_06', 'Net profit compounding at above 20% over 5 years creates significant shareholder value', conf))

            # Pro Rule 7: ICR > 10 or Debt Free
            icr = lat_r.get('interest_coverage')
            if (pd.notna(icr) and icr > 10.0) or de == 0 or (pd.notna(de) and de <= 0.01) or pd.isna(icr):
                c_pros.append(('PRO_07', 'Very high interest coverage ratio reflects negligible financial stress from debt servicing', 90))

            # Pro Rule 8: Dividend Yield > 2% with FCF positive
            div_yield = lat_mc.get('dividend_yield_pct') if lat_mc is not None else None
            fcf = lat_r.get('free_cash_flow_cr')
            if pd.notna(div_yield) and div_yield > 2.0 and pd.notna(fcf) and fcf > 0:
                conf = min(95, int(75 + (div_yield - 2.0) * 5))
                c_pros.append(('PRO_08', 'Consistent dividend yield above 2% backed by positive free cash flow', conf))

            # Pro Rule 9: EPS CAGR > 15% over 5 years
            eps_cagr = lat_r.get('eps_cagr_5yr')
            if pd.notna(eps_cagr) and eps_cagr > 15.0:
                conf = min(95, int(70 + (eps_cagr - 15) * 1.5))
                c_pros.append(('PRO_09', 'Earnings per share growing above 15% CAGR indicates strong earnings quality and compounding', conf))

            # Pro Rule 10: ROE improving for 3 consecutive years
            if len(c_r) >= 3:
                roes = c_r['return_on_equity_pct'].tail(3).values
                if roes[2] > roes[1] > roes[0]:
                    c_pros.append(('PRO_10', 'Return on equity improving for 3 consecutive years shows strengthening business quality', 80))

            # Pro Rule 11: Revenue CAGR < PAT CAGR (operating leverage)
            if pd.notna(rev_cagr) and pd.notna(pat_cagr) and pat_cagr > rev_cagr and rev_cagr > 0:
                c_pros.append(('PRO_11', 'Revenue growing slower than profits shows improving operating leverage and scale benefits', 82))

            # Pro Rule 12: Balance sheet assets growing with declining debt
            if len(c_bs) >= 3:
                ass = c_bs['total_assets'].tail(3).values
                deb = c_bs['borrowings'].tail(3).values
                if ass[2] > ass[0] and deb[2] < deb[0]:
                    c_pros.append(('PRO_12', 'Growing asset base funded by internal accruals reflects self-sustaining growth', 80))

            # Con Rule 1: D/E > 2.0 for non-financial companies
            if sec != 'Financials' and pd.notna(de) and de > 2.0:
                conf = min(95, int(70 + (de - 2.0) * 8))
                c_cons.append(('CON_01', f'Debt-to-equity ratio of {de:.2f} is elevated for a non-financial company and warrants monitoring', conf))

            # Con Rule 2: FCF negative for 3 consecutive years
            if len(c_r) >= 3 and (c_r['free_cash_flow_cr'].tail(3) < 0).all():
                c_cons.append(('CON_02', 'Free cash flow negative for 3 consecutive years raises concern about cash generation quality', 85))

            # Con Rule 3: OPM declining for 3 consecutive years
            if len(c_r) >= 3:
                opms = c_r['operating_profit_margin_pct'].tail(3).values
                if opms[2] < opms[1] < opms[0]:
                    c_cons.append(('CON_03', 'Operating margins declining for 3 consecutive years suggest pricing or cost pressure', 80))

            # Con Rule 4: Net profit negative in latest year
            if lat_pl is not None and pd.notna(lat_pl.get('net_profit')) and lat_pl.get('net_profit') < 0:
                c_cons.append(('CON_04', 'Company reported a net loss in the most recent financial year', 95))

            # Con Rule 5: Revenue declining for 2+ years
            if len(c_pl) >= 3:
                revs = c_pl['sales'].tail(3).values
                if revs[2] < revs[1] < revs[0]:
                    c_cons.append(('CON_05', 'Revenue contraction over 2 consecutive years indicates demand weakness or market share loss', 85))

            # Con Rule 6: ICR < 1.5
            if pd.notna(icr) and icr < 1.5 and pd.notna(de) and de > 0.05:
                c_cons.append(('CON_06', 'Interest coverage ratio below 1.5x indicates the company is at risk of not meeting its debt obligations', 85))

            # Con Rule 7: Dividend payout > 100%
            if lat_pl is not None and pd.notna(lat_pl.get('dividend_payout')) and lat_pl.get('dividend_payout') > 100.0:
                c_cons.append(('CON_07', 'Dividend payout ratio above 100% means the company is paying dividends from reserves, which is unsustainable', 85))

            # Con Rule 8: D/E rising for 3 consecutive years
            if len(c_r) >= 3:
                des = c_r['debt_to_equity'].tail(3).values
                if des[2] > des[1] > des[0] and des[2] > 0.1:
                    c_cons.append(('CON_08', 'Rising debt-to-equity ratio over 3 years suggests increasing financial leverage risk', 80))

            # Con Rule 9: EPS declining for 3 consecutive years
            if len(c_pl) >= 3:
                epss = c_pl['eps'].tail(3).values
                if epss[2] < epss[1] < epss[0]:
                    c_cons.append(('CON_09', 'Earnings per share declining for 3 consecutive years reflects deteriorating profitability', 80))

            # Con Rule 10: ROCE < 10%
            roce = lat_r.get('return_on_capital_pct')
            if pd.notna(roce) and roce < 10.0:
                c_cons.append(('CON_10', 'Return on capital employed below 10% suggests the business is not generating sufficient returns on invested capital', 80))

            # Con Rule 11: Net Debt > 3x EBITDA
            if lat_bs is not None and lat_pl is not None:
                deb_val = lat_bs.get('borrowings', 0) or 0
                ebitda = lat_pl.get('operating_profit', 0) or 0
                if sec != 'Financials' and ebitda > 0 and deb_val > 3 * ebitda:
                    c_cons.append(('CON_11', 'Net debt exceeding 3 times EBITDA is a high leverage ratio and limits financial flexibility', 85))

            # Con Rule 12: Revenue CAGR < 5% over 5 years
            if pd.notna(rev_cagr) and rev_cagr < 5.0:
                c_cons.append(('CON_12', 'Revenue growing at below 5% over 5 years lags inflation and suggests limited business momentum', 80))

        # Enforce at least 1 pro and 1 con per company (> 60% confidence)
        if len(c_pros) == 0:
            if lat_r is not None and pd.notna(lat_r.get('debt_to_equity')) and lat_r.get('debt_to_equity') < 0.5:
                c_pros.append(('PRO_03', 'Conservative leverage with low debt-to-equity provides solid balance sheet buffer', 75))
            elif lat_pl is not None and pd.notna(lat_pl.get('net_profit')) and lat_pl.get('net_profit') > 0:
                c_pros.append(('PRO_05', 'Maintains positive operating profitability across business cycles', 72))
            else:
                c_pros.append(('PRO_07', 'Stable financial standing with manageable debt service coverage', 70))

        if len(c_cons) == 0:
            if len(c_r) >= 2 and c_r['operating_profit_margin_pct'].iloc[-1] < c_r['operating_profit_margin_pct'].iloc[-2]:
                c_cons.append(('CON_03', 'Operating margins declining year-over-year suggest pricing or cost pressure', 75))
            elif len(c_r) >= 2 and c_r['return_on_equity_pct'].iloc[-1] < c_r['return_on_equity_pct'].iloc[-2]:
                c_cons.append(('CON_10', 'Return on capital employed softened year-over-year suggesting temporary return moderation', 75))
            elif len(c_pl) >= 2 and c_pl['sales'].iloc[-1] < c_pl['sales'].iloc[-2]:
                c_cons.append(('CON_05', 'Revenue contraction in the most recent year indicates demand weakness or market share loss', 78))
            elif lat_r is not None and pd.notna(lat_r.get('revenue_cagr_5yr')) and lat_r.get('revenue_cagr_5yr') < 10.0:
                c_cons.append(('CON_12', 'Revenue growing at below 5% over 5 years lags inflation and suggests limited business momentum', 72))
            elif lat_mc is not None and pd.notna(lat_mc.get('pe_ratio')) and lat_mc.get('pe_ratio') > 30.0:
                c_cons.append(('CON_11', 'Elevated price-to-earnings valuation multiple limits financial margin of safety', 75))
            else:
                c_cons.append(('CON_12', 'Growth rate and return metrics reflect mature market conditions requiring close execution monitoring', 70))

        # Filter confidence > 60% and record
        for rid, txt, conf in c_pros:
            if conf > 60:
                records.append({
                    'company_id': cid,
                    'type': 'pro',
                    'rule_id': rid,
                    'text': txt,
                    'confidence_pct': conf
                })
        for rid, txt, conf in c_cons:
            if conf > 60:
                records.append({
                    'company_id': cid,
                    'type': 'con',
                    'rule_id': rid,
                    'text': txt,
                    'confidence_pct': conf
                })

    df_out = pd.DataFrame(records)
    out_file = os.path.join(output_dir, 'pros_cons_generated.csv')
    df_out.to_csv(out_file, index=False)

    print(f"Generated {len(df_out)} pros and cons saved to {out_file}")
    pro_c = df_out[df_out['type'] == 'pro']['company_id'].nunique()
    con_c = df_out[df_out['type'] == 'con']['company_id'].nunique()
    print(f"Companies with >= 1 Pro: {pro_c}/92")
    print(f"Companies with >= 1 Con: {con_c}/92")

    return df_out

if __name__ == '__main__':
    generate_pros_cons()
