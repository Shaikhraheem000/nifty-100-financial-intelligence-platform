import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st

st.set_page_config(
    page_title="Nifty 100 Analytics",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Navigation
st.sidebar.title("Nifty 100 Analytics")
st.sidebar.markdown("Navigate through the analytics modules using the pages above.")

st.write("# Nifty 100 Analytics Platform")
st.write("Welcome to the Nifty 100 Financial Intelligence Streamlit Dashboard.")
st.write("Please select a page from the sidebar to begin exploring the data:")
st.markdown("""
- **01 - Home**: Market overview, 6 KPI cards, sector donut chart, and top 5 quality compounders.
- **02 - Company Profile**: Deep dive into individual companies, 10-year financials, dual-axis charts, and pros/cons.
- **03 - Screener**: Interactive multi-metric filtering with 6 one-click presets and CSV export.
- **04 - Peer Comparison**: Radar charts and side-by-side benchmarking against sector peers.
- **05 - Trend Analysis**: 10-year multi-metric overlay with year-over-year growth trajectories.
- **06 - Sector Analysis**: Revenue vs ROE bubble chart scaled by market cap and median KPI benchmarks.
- **07 - Capital Allocation**: Treemap visualization of cash flow allocation patterns across the index.
- **08 - Annual Reports**: Direct access and status validation for company BSE annual report filings.
""")
