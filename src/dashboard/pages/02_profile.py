import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3

try:
    from src.dashboard.utils.db import get_companies, get_ratios, get_pl, get_sectors
except ModuleNotFoundError:
    from utils.db import get_companies, get_ratios, get_pl, get_sectors

st.title("02 - Company Profile")

companies = get_companies()
sectors = get_sectors()

# Text search
search_query = st.selectbox(
    "Search for a company (Ticker or Name)",
    options=[""] + sorted(companies['id'].tolist()) + sorted(companies['company_name'].tolist())
)

if search_query == "":
    st.write("Please select or type a company name/ticker.")
else:
    # Resolve ticker
    if search_query in companies['id'].tolist():
        ticker = search_query
    elif search_query in companies['company_name'].tolist():
        ticker = companies[companies['company_name'] == search_query]['id'].values[0]
    else:
        st.error("Ticker not found — please try another")
        ticker = None
        
    if ticker:
        comp_info = companies[companies['id'] == ticker].iloc[0]
        sec_info = sectors[sectors['company_id'] == ticker]
        
        c_sector = sec_info['broad_sector'].values[0] if not sec_info.empty else "N/A"
        c_subsector = sec_info['sub_sector'].values[0] if not sec_info.empty else "N/A"
        
        st.markdown(f"### {comp_info['company_name']} ({ticker})")
        st.write(f"**Sector:** {c_sector} | **Sub-Sector:** {c_subsector}")
        
        # Load data
        pl = get_pl(ticker)
        ratios = get_ratios(ticker)
        
        # KPI Tiles (Latest Year)
        if not ratios.empty:
            ratios['year_dt'] = pd.to_datetime(ratios['year'])
            latest_r = ratios.loc[ratios['year_dt'].idxmax()]
            
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            c1.metric("ROE", f"{latest_r.get('return_on_equity_pct', 'N/A')}%")
            c2.metric("ROCE", f"{latest_r.get('return_on_capital_pct', 'N/A')}%")
            c3.metric("NPM", f"{latest_r.get('net_profit_margin_pct', 'N/A')}%")
            c4.metric("D/E", f"{latest_r.get('debt_to_equity', 'N/A')}")
            c5.metric("Rev CAGR 5Y", f"{latest_r.get('revenue_cagr_5yr', 'N/A')}%")
            c6.metric("FCF", f"₹{latest_r.get('free_cash_flow_cr', 'N/A')} Cr")
            
        st.write("---")
        
        if not pl.empty:
            pl_sorted = pl.sort_values('year')
            # 10-year bar chart for Rev and NP
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(x=pl_sorted['year'], y=pl_sorted['sales'], name='Revenue'))
            fig_bar.add_trace(go.Bar(x=pl_sorted['year'], y=pl_sorted['net_profit'], name='Net Profit'))
            fig_bar.update_layout(title="Revenue & Net Profit (10 Years)", barmode='group')
            st.plotly_chart(fig_bar, use_container_width=True)
            
        if not ratios.empty:
            r_sorted = ratios.sort_values('year_dt')
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(x=r_sorted['year'], y=r_sorted['return_on_equity_pct'], name='ROE %', mode='lines+markers'))
            fig_line.add_trace(go.Scatter(x=r_sorted['year'], y=r_sorted['return_on_capital_pct'], name='ROCE %', mode='lines+markers', yaxis='y2'))
            fig_line.update_layout(
                title="ROE & ROCE Trend (10 Years)",
                yaxis=dict(title='ROE %'),
                yaxis2=dict(title='ROCE %', overlaying='y', side='right')
            )
            st.plotly_chart(fig_line, use_container_width=True)
            
        # Pros and Cons
        st.write("---")
        st.write("### Pros and Cons")
        db_path = os.path.join(ROOT_DIR, 'data', 'nifty100.db')
        shown_any = False
        with sqlite3.connect(db_path) as conn:
            procons = pd.read_sql("SELECT * FROM prosandcons WHERE company_id = ?", conn, params=[ticker])
            if not procons.empty:
                for _, row in procons.iterrows():
                    if 'pros' in row and pd.notna(row['pros']) and str(row['pros']).strip():
                        st.markdown(f"✅ {row['pros']}")
                        shown_any = True
                    if 'cons' in row and pd.notna(row['cons']) and str(row['cons']).strip():
                        st.markdown(f"❌ {row['cons']}")
                        shown_any = True
        
        # Check generated NLP pros/cons if DB had none
        gen_path = os.path.join(ROOT_DIR, 'output', 'pros_cons_generated.csv')
        if not shown_any and os.path.exists(gen_path):
            gen_df = pd.read_csv(gen_path)
            c_gen = gen_df[gen_df['company_id'] == ticker]
            if not c_gen.empty:
                for _, r in c_gen.iterrows():
                    icon = "✅" if r['type'] == 'Pro' else "❌"
                    st.markdown(f"{icon} {r['text']}")
                    shown_any = True
                    
        if not shown_any:
            st.write("No pros/cons data available.")
