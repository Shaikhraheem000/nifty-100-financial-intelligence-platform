import sqlite3
import pandas as pd
import streamlit as st
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
DB_PATH = os.path.join(PROJECT_ROOT, 'data', 'nifty100.db')

@st.cache_data(ttl=600)
def get_companies():
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql("SELECT * FROM companies", conn)

@st.cache_data(ttl=600)
def get_ratios(ticker=None, year=None):
    with sqlite3.connect(DB_PATH) as conn:
        query = "SELECT * FROM financial_ratios WHERE 1=1"
        params = []
        if ticker:
            query += " AND company_id = ?"
            params.append(ticker)
        if year:
            query += " AND year = ?"
            params.append(year)
        return pd.read_sql(query, conn, params=params)

@st.cache_data(ttl=600)
def get_pl(ticker=None):
    with sqlite3.connect(DB_PATH) as conn:
        query = "SELECT * FROM profitandloss"
        if ticker:
            query += " WHERE company_id = ?"
            return pd.read_sql(query, conn, params=[ticker])
        return pd.read_sql(query, conn)

@st.cache_data(ttl=600)
def get_bs(ticker=None):
    with sqlite3.connect(DB_PATH) as conn:
        query = "SELECT * FROM balancesheet"
        if ticker:
            query += " WHERE company_id = ?"
            return pd.read_sql(query, conn, params=[ticker])
        return pd.read_sql(query, conn)

@st.cache_data(ttl=600)
def get_cf(ticker=None):
    with sqlite3.connect(DB_PATH) as conn:
        query = "SELECT * FROM cashflow"
        if ticker:
            query += " WHERE company_id = ?"
            return pd.read_sql(query, conn, params=[ticker])
        return pd.read_sql(query, conn)

@st.cache_data(ttl=600)
def get_sectors():
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql("SELECT * FROM sectors", conn)

@st.cache_data(ttl=600)
def get_peers(group_name=None):
    with sqlite3.connect(DB_PATH) as conn:
        if group_name:
            # First try to get from peer_percentiles if it exists
            try:
                return pd.read_sql("SELECT * FROM peer_percentiles WHERE peer_group_name = ?", conn, params=[group_name])
            except sqlite3.OperationalError:
                return pd.DataFrame()
        else:
            try:
                return pd.read_sql("SELECT DISTINCT peer_group_name FROM peer_percentiles", conn)
            except sqlite3.OperationalError:
                return pd.DataFrame()

@st.cache_data(ttl=600)
def get_valuation(ticker=None):
    val_path = os.path.join(PROJECT_ROOT, 'output', 'valuation_summary.xlsx')
    if os.path.exists(val_path):
        df = pd.read_excel(val_path)
        if ticker:
            return df[df['company_id'] == ticker]
        return df
    return pd.DataFrame()
