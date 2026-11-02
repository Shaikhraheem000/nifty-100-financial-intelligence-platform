import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st
import pandas as pd
import sqlite3
import requests

st.title("08 - Annual Reports")

db_path = os.path.join(ROOT_DIR, 'data', 'nifty100.db')

with sqlite3.connect(db_path) as conn:
    companies = pd.read_sql("SELECT id as company_id, company_name FROM companies", conn)

search_query = st.selectbox(
    "Search for a company (Ticker or Name)",
    options=[""] + sorted(companies['company_id'].tolist()) + sorted(companies['company_name'].tolist())
)

if search_query != "":
    if search_query in companies['company_id'].tolist():
        ticker = search_query
    else:
        ticker = companies[companies['company_name'] == search_query]['company_id'].values[0]
        
    with sqlite3.connect(db_path) as conn:
        docs = pd.read_sql("SELECT year, annual_report as bse_url FROM documents WHERE company_id = ? ORDER BY year DESC", conn, params=[ticker])
        
    if not docs.empty:
        st.write(f"### Annual Reports for {ticker}")
        
        for _, row in docs.iterrows():
            year = row['year']
            url = row['bse_url']
            
            col1, col2 = st.columns([1, 4])
            col1.write(f"**{year}**")
            
            if url and pd.notna(url):
                # Optionally check 404
                try:
                    r = requests.head(url, timeout=2)
                    if r.status_code == 404:
                        col2.markdown(f"🚨 **[Report unavailable]({url})** (404)")
                    else:
                        col2.markdown(f"📄 [View Report]({url})")
                except Exception:
                    col2.markdown(f"📄 [View Report]({url})")
            else:
                col2.markdown("🚨 **Report unavailable**")
    else:
        st.write("No reports found for this company.")
