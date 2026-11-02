import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st
import pandas as pd
import plotly.express as px

st.title("07 - Capital Allocation Map")

cap_alloc_path = os.path.join(ROOT_DIR, 'output', 'capital_allocation.csv')

if os.path.exists(cap_alloc_path):
    df = pd.read_csv(cap_alloc_path)
    df = df.sort_values('year').drop_duplicates('company_id', keep='last')
    
    df['Platform'] = 'Nifty 100'
    df['count'] = 1
    
    fig = px.treemap(
        df,
        path=['Platform', 'pattern', 'company_id'],
        values='count',
        color='pattern',
        title="Capital Allocation Patterns (Latest Year)"
    )
    fig.update_traces(root_color="lightgrey")
    fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.write("### Companies by Pattern")
    selected_pattern = st.selectbox("Select Pattern to view companies", options=sorted(df['pattern'].unique()))
    
    if selected_pattern:
        pattern_df = df[df['pattern'] == selected_pattern][['company_id', 'cfo', 'cfi', 'cff']]
        st.dataframe(pattern_df)
else:
    st.write("capital_allocation.csv not found.")
