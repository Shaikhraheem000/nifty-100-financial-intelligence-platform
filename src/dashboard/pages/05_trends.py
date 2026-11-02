import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

try:
    from src.dashboard.utils.db import get_companies, get_ratios, get_pl, get_bs, get_cf
except ModuleNotFoundError:
    from utils.db import get_companies, get_ratios, get_pl, get_bs, get_cf

st.title("05 - Trend Analysis")

companies = get_companies()
search_query = st.selectbox(
    "Search for a company (Ticker or Name)",
    options=[""] + sorted(companies['id'].tolist()) + sorted(companies['company_name'].tolist())
)

if search_query != "":
    if search_query in companies['id'].tolist():
        ticker = search_query
    else:
        ticker = companies[companies['company_name'] == search_query]['id'].values[0]
        
    ratios = get_ratios(ticker)
    pl = get_pl(ticker)
    bs = get_bs(ticker)
    cf = get_cf(ticker)
    
    # Merge them together for metrics
    ratios['year'] = ratios['year'].astype(str)
    pl['year'] = pl['year'].astype(str)
    bs['year'] = bs['year'].astype(str)
    cf['year'] = cf['year'].astype(str)
    
    # Standardise year prefix
    ratios['year_prefix'] = ratios['year'].str[:4]
    pl['year_prefix'] = pl['year'].str[:4]
    bs['year_prefix'] = bs['year'].str[:4]
    cf['year_prefix'] = cf['year'].str[:4]
    
    df = ratios.merge(pl, on='year_prefix', how='outer', suffixes=('', '_pl'))
    df = df.merge(bs, on='year_prefix', how='outer', suffixes=('', '_bs'))
    df = df.merge(cf, on='year_prefix', how='outer', suffixes=('', '_cf'))
    
    df = df.sort_values('year_prefix')
    
    available_metrics = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c not in ['company_id', 'year', 'year_prefix', 'year_pl', 'year_bs', 'year_cf']]
    
    selected_metrics = st.multiselect("Select up to 3 metrics to overlay", options=available_metrics, max_selections=3)
    
    if selected_metrics:
        fig = go.Figure()
        
        for metric in selected_metrics:
            valid_df = df.dropna(subset=[metric])
            if valid_df.empty:
                continue
                
            x = valid_df['year_prefix']
            y = valid_df[metric]
            
            # Calculate YoY change
            yoy = y.pct_change() * 100
            text = [f"{v:.1f}%" if pd.notna(v) else "" for v in yoy]
            
            fig.add_trace(go.Scatter(
                x=x, y=y, name=metric, mode='lines+markers+text',
                text=text, textposition="top center"
            ))
            
        fig.update_layout(title="10-Year Trend Analysis", xaxis_title="Year")
        st.plotly_chart(fig, use_container_width=True)
