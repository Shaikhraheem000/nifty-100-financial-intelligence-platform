import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

try:
    from src.dashboard.utils.db import get_peers, get_companies
except ModuleNotFoundError:
    from utils.db import get_peers, get_companies

st.title("04 - Peer Comparison")

peer_groups = get_peers()
if peer_groups.empty:
    st.write("No peer group data found.")
else:
    group_names = sorted(peer_groups['peer_group_name'].unique().tolist())
    selected_group = st.selectbox("Select Peer Group", options=group_names)
    
    if selected_group:
        peers_df = get_peers(selected_group)
        companies = get_companies()
        
        # Merge company names
        peers_df = peers_df.merge(companies[['id', 'company_name']], left_on='company_id', right_on='id', how='left')
        
        # Get latest year for radar
        latest_year = peers_df['year'].max()
        latest_peers = peers_df[peers_df['year'] == latest_year]
        
        # Dropdown for radar chart company
        c_list = sorted(latest_peers['company_name'].dropna().unique().tolist())
        if c_list:
            selected_comp = st.selectbox("Select Company for Radar Chart", options=c_list)
            
            c_data = latest_peers[latest_peers['company_name'] == selected_comp]
            
            if not c_data.empty:
                metrics = [
                    'return_on_equity_pct', 'return_on_capital_pct', 'net_profit_margin_pct',
                    'debt_to_equity', 'free_cash_flow_cr', 'pat_cagr_5yr', 'revenue_cagr_5yr', 'eps_cagr_5yr'
                ]
                
                # Fetch percentiles for this company
                vals = []
                for m in metrics:
                    row = c_data[c_data['metric'] == m]
                    vals.append(row['percentile_rank'].iloc[0] if not row.empty else 0.5)
                    
                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(
                    r=vals + [vals[0]],
                    theta=metrics + [metrics[0]],
                    fill='toself',
                    name=selected_comp,
                    line_color='blue'
                ))
                
                # Peer average (50th percentile)
                avgs = [0.5] * len(metrics)
                fig.add_trace(go.Scatterpolar(
                    r=avgs + [avgs[0]],
                    theta=metrics + [metrics[0]],
                    mode='lines',
                    line_color='gray',
                    line_dash='dash',
                    name=f'{selected_group} Avg'
                ))
                
                fig.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                    showlegend=True,
                    title=f"{selected_comp} vs {selected_group} Average"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
        st.write("---")
        st.write("### Side-by-Side KPI Table")
        
        peer_excel = os.path.join(ROOT_DIR, 'output', 'peer_comparison.xlsx')
        if os.path.exists(peer_excel):
            try:
                sheet_name = selected_group[:31].replace('/', '_')
                df_excel = pd.read_excel(peer_excel, sheet_name=sheet_name)
                st.dataframe(df_excel)
            except Exception as e:
                st.write("Could not load Excel sheet.", e)
        else:
            st.write("peer_comparison.xlsx not found.")
