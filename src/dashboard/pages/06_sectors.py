import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3

try:
    from src.dashboard.utils.db import get_companies, get_sectors, get_ratios, get_pl
except ModuleNotFoundError:
    from utils.db import get_companies, get_sectors, get_ratios, get_pl

st.title("06 - Sector Analysis")

sectors = get_sectors()
broad_sectors = sorted(sectors['broad_sector'].dropna().unique().tolist())

selected_sector = st.selectbox("Select Sector", options=broad_sectors)

if selected_sector:
    sec_df = sectors[sectors['broad_sector'] == selected_sector]
    c_ids = sec_df['company_id'].tolist()
    
    # Load ratios, pl, mc
    ratios = get_ratios()
    ratios['year_dt'] = pd.to_datetime(ratios['year'])
    latest_r = ratios.loc[ratios.groupby('company_id')['year_dt'].idxmax()]
    
    pl = get_pl()
    latest_pl = pl.loc[pl.groupby('company_id')['year'].idxmax()]
    
    # Market Cap
    db_path = os.path.join(ROOT_DIR, 'data', 'nifty100.db')
    with sqlite3.connect(db_path) as conn:
        mc = pd.read_sql("SELECT company_id, year, market_cap_crore FROM market_cap", conn)
    latest_mc = mc.loc[mc.groupby('company_id')['year'].idxmax()]
    
    # Merge
    df = sec_df.merge(latest_r[['company_id', 'return_on_equity_pct', 'debt_to_equity', 'net_profit_margin_pct']], on='company_id', how='left')
    df = df.merge(latest_pl[['company_id', 'sales']], on='company_id', how='left')
    df = df.merge(latest_mc[['company_id', 'market_cap_crore']], on='company_id', how='left')
    companies = get_companies()
    df = df.merge(companies[['id', 'company_name']], left_on='company_id', right_on='id', how='left')
    
    df['market_cap_crore'] = df['market_cap_crore'].fillna(1000)
    
    fig = px.scatter(
        df,
        x='sales',
        y='return_on_equity_pct',
        size='market_cap_crore',
        color='sub_sector',
        hover_name='company_name',
        title=f"Sector Bubble Chart: {selected_sector} (X=Revenue, Y=ROE, Size=Market Cap)"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.write("---")
    st.write("### Sector Median KPIs")
    medians = df[['return_on_equity_pct', 'debt_to_equity', 'net_profit_margin_pct']].median().reset_index()
    medians.columns = ['KPI', 'Median Value']
    
    fig_bar = px.bar(medians, x='KPI', y='Median Value', title=f"Median KPIs for {selected_sector}")
    st.plotly_chart(fig_bar, use_container_width=True)
