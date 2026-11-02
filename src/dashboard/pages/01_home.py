import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st
import pandas as pd
import plotly.express as px

try:
    from src.dashboard.utils.db import get_companies, get_ratios, get_sectors, get_valuation
except ModuleNotFoundError:
    from utils.db import get_companies, get_ratios, get_sectors, get_valuation

st.title("01 - Home")

# Global year selector
year = st.sidebar.selectbox("Select Year", options=['2024-03', '2023-03', '2022-03', '2021-03', '2020-03', '2019-03'])
st.write(f"### Financial Summary for {year}")

# Load data
companies = get_companies()
sectors = get_sectors()
ratios = get_ratios(year=year)
valuation = get_valuation()

# Calculate KPIs
total_companies = len(companies)

avg_roe = ratios['return_on_equity_pct'].mean() if not ratios.empty else 0
med_de = ratios['debt_to_equity'].median() if not ratios.empty else 0
med_rev_cagr = ratios['revenue_cagr_5yr'].median() if not ratios.empty else 0
debt_free_count = len(ratios[ratios['debt_to_equity'] == 0]) if not ratios.empty else 0
med_pe = valuation['pe_ratio'].median() if not valuation.empty else 0

# Display KPIs
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Total Companies", total_companies)
c2.metric("Average ROE", f"{avg_roe:.2f}%" if pd.notna(avg_roe) else "N/A")
c3.metric("Median P/E", f"{med_pe:.2f}" if pd.notna(med_pe) else "N/A")
c4.metric("Median D/E", f"{med_de:.2f}" if pd.notna(med_de) else "N/A")
c5.metric("Median Rev CAGR 5Y", f"{med_rev_cagr:.2f}%" if pd.notna(med_rev_cagr) else "N/A")
c6.metric("Debt-Free Count", debt_free_count)

# Sector Breakdown Donut
st.write("---")
st.write("### Sector Breakdown")
sec_counts = sectors['broad_sector'].value_counts().reset_index()
sec_counts.columns = ['Sector', 'Count']
fig = px.pie(sec_counts, values='Count', names='Sector', hole=0.4, title='Companies per Sector')
st.plotly_chart(fig, use_container_width=True)

# Top 5 Composite Quality Score
st.write("---")
st.write("### Top 5 Companies by Composite Quality Score")
if 'composite_score' in ratios.columns:
    top5 = ratios.sort_values('composite_score', ascending=False).head(5)
    top5 = top5[['company_id', 'composite_score', 'return_on_equity_pct', 'debt_to_equity', 'free_cash_flow_cr']]
    top5 = top5.merge(companies[['id', 'company_name']], left_on='company_id', right_on='id', how='left')
    st.dataframe(top5[['company_name', 'composite_score', 'return_on_equity_pct', 'debt_to_equity', 'free_cash_flow_cr']])
else:
    screener_path = os.path.join(ROOT_DIR, 'output', 'screener_output.xlsx')
    if os.path.exists(screener_path):
        top_df = pd.read_excel(screener_path, sheet_name='Quality')
        st.dataframe(top_df.head(5))
    else:
        st.write("Composite score data not found. Please run the screener export first.")
