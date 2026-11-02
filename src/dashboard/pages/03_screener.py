import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st
import pandas as pd
import sqlite3

try:
    from src.dashboard.utils.db import get_ratios, get_companies, get_sectors, get_valuation
except ModuleNotFoundError:
    from utils.db import get_ratios, get_companies, get_sectors, get_valuation

st.title("03 - Screener")

# State for sliders
if 'preset' not in st.session_state:
    st.session_state.update({
        'roe_min': 0.0, 'de_max': 5.0, 'fcf_min': -10000.0,
        'rev_cagr_min': -20.0, 'pat_cagr_min': -20.0, 'opm_min': 0.0,
        'pe_max': 100.0, 'pb_max': 20.0, 'div_yield_min': 0.0, 'icr_min': 0.0
    })

def set_preset(preset):
    # Reset first
    st.session_state.update({
        'roe_min': 0.0, 'de_max': 10.0, 'fcf_min': -50000.0,
        'rev_cagr_min': -50.0, 'pat_cagr_min': -50.0, 'opm_min': -50.0,
        'pe_max': 200.0, 'pb_max': 50.0, 'div_yield_min': 0.0, 'icr_min': -10.0
    })
    
    if preset == 'Quality':
        st.session_state['roe_min'] = 15.0
        st.session_state['de_max'] = 1.0
        st.session_state['fcf_min'] = 0.0
    elif preset == 'Value':
        st.session_state['pe_max'] = 20.0
        st.session_state['pb_max'] = 3.0
        st.session_state['de_max'] = 2.0
    elif preset == 'Growth':
        st.session_state['pat_cagr_min'] = 20.0
        st.session_state['rev_cagr_min'] = 15.0
        st.session_state['de_max'] = 2.0
    elif preset == 'Dividend':
        st.session_state['div_yield_min'] = 2.0
        st.session_state['fcf_min'] = 0.0
    elif preset == 'Debt-Free':
        st.session_state['de_max'] = 0.0
        st.session_state['roe_min'] = 12.0
    elif preset == 'Turnaround':
        st.session_state['rev_cagr_min'] = 10.0
        st.session_state['fcf_min'] = 0.0

st.sidebar.markdown("### Presets")
col1, col2 = st.sidebar.columns(2)
if col1.button("Quality"): set_preset("Quality")
if col2.button("Value"): set_preset("Value")
if col1.button("Growth"): set_preset("Growth")
if col2.button("Dividend"): set_preset("Dividend")
if col1.button("Debt-Free"): set_preset("Debt-Free")
if col2.button("Turnaround"): set_preset("Turnaround")

st.sidebar.markdown("### Filters")
roe = st.sidebar.slider("ROE Min (%)", -50.0, 100.0, st.session_state['roe_min'], key='roe_min')
de = st.sidebar.slider("D/E Max", 0.0, 10.0, st.session_state['de_max'], key='de_max')
fcf = st.sidebar.slider("FCF Min (Cr)", -50000.0, 50000.0, float(st.session_state['fcf_min']), key='fcf_min')
rev_cagr = st.sidebar.slider("Revenue CAGR 5Y Min (%)", -50.0, 100.0, st.session_state['rev_cagr_min'], key='rev_cagr_min')
pat_cagr = st.sidebar.slider("PAT CAGR 5Y Min (%)", -50.0, 100.0, st.session_state['pat_cagr_min'], key='pat_cagr_min')
opm = st.sidebar.slider("OPM Min (%)", -50.0, 100.0, st.session_state['opm_min'], key='opm_min')
pe = st.sidebar.slider("P/E Max", 0.0, 200.0, st.session_state['pe_max'], key='pe_max')
pb = st.sidebar.slider("P/B Max", 0.0, 50.0, st.session_state['pb_max'], key='pb_max')
div_yield = st.sidebar.slider("Dividend Yield Min (%)", 0.0, 20.0, st.session_state['div_yield_min'], key='div_yield_min')
icr = st.sidebar.slider("ICR Min", -10.0, 50.0, st.session_state['icr_min'], key='icr_min')

# Load latest data
ratios = get_ratios()
ratios['year_dt'] = pd.to_datetime(ratios['year'])
idx = ratios.groupby('company_id')['year_dt'].idxmax()
df = ratios.loc[idx].copy()

companies = get_companies()
sectors = get_sectors()
valuation = get_valuation()

df = df.merge(companies[['id', 'company_name']], left_on='company_id', right_on='id', how='left')
df = df.merge(sectors[['company_id', 'broad_sector']], on='company_id', how='left')
if not valuation.empty:
    df = df.merge(valuation[['company_id', 'pe_ratio', 'pb_ratio']], on='company_id', how='left')

db_path = os.path.join(ROOT_DIR, 'data', 'nifty100.db')
with sqlite3.connect(db_path) as conn:
    mc = pd.read_sql("SELECT company_id, pe_ratio as pe_ratio_mc, pb_ratio as pb_ratio_mc, dividend_yield_pct FROM market_cap", conn)
    mc_idx = mc.groupby('company_id').tail(1)
    df = df.merge(mc_idx, on='company_id', how='left')
    
    if 'pe_ratio' not in df.columns or df['pe_ratio'].isna().all():
        df['pe_ratio'] = df['pe_ratio_mc']
    if 'pb_ratio' not in df.columns or df['pb_ratio'].isna().all():
        df['pb_ratio'] = df['pb_ratio_mc']
        
    screen_path = os.path.join(ROOT_DIR, 'output', 'screener_output.xlsx')
    if os.path.exists(screen_path):
        scores = pd.read_excel(screen_path, sheet_name='Quality')[['company_name', 'composite_score']]
        df = df.merge(scores, on='company_name', how='left')
    else:
        df['composite_score'] = "N/A"

# Apply Filters
res = df.copy()
res = res[(res['return_on_equity_pct'].fillna(-999) >= roe)]
res = res[(res['debt_to_equity'].fillna(0) <= de) | (res['broad_sector'] == 'Financials')]
res = res[(res['free_cash_flow_cr'].fillna(-99999) >= fcf)]
res = res[(res['revenue_cagr_5yr'].fillna(-999) >= rev_cagr)]
res = res[(res['pat_cagr_5yr'].fillna(-999) >= pat_cagr)]
res = res[(res['operating_profit_margin_pct'].fillna(-999) >= opm)]
res = res[(res['pe_ratio'].fillna(9999) <= pe)]
res = res[(res['pb_ratio'].fillna(9999) <= pb)]
res = res[(res['dividend_yield_pct'].fillna(0) >= div_yield)]
res = res[(res['interest_coverage'].fillna(9999) >= icr)]

st.write(f"### {len(res)} companies match your filters")

display_cols = [
    'company_id', 'company_name', 'broad_sector', 'composite_score',
    'return_on_equity_pct', 'debt_to_equity', 'free_cash_flow_cr',
    'revenue_cagr_5yr', 'pat_cagr_5yr', 'operating_profit_margin_pct',
    'pe_ratio', 'pb_ratio', 'dividend_yield_pct', 'interest_coverage'
]

display_df = res[[c for c in display_cols if c in res.columns]]
st.dataframe(display_df)

csv = display_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Download CSV",
    data=csv,
    file_name='screener_results.csv',
    mime='text/csv',
)
