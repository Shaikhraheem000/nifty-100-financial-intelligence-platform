"""
Peer group analytics, percentile rankings, and radar benchmark comparison router.
"""

from fastapi import APIRouter, Depends, HTTPException
import sqlite3
import pandas as pd
from src.api.db import get_db

router = APIRouter(tags=["Peers"])

RADAR_METRICS = [
    'return_on_equity_pct',
    'return_on_capital_pct',
    'net_profit_margin_pct',
    'debt_to_equity',
    'free_cash_flow_cr',
    'pat_cagr_5yr',
    'revenue_cagr_5yr',
    'eps_cagr_5yr'
]


@router.get("/peers/{group_name}")
def get_peer_group_percentiles(group_name: str, conn: sqlite3.Connection = Depends(get_db)):
    """Return all constituent companies in a peer group with their computed percentile rankings across 10 metrics."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT peer_group_name 
        FROM peer_percentiles 
        WHERE UPPER(peer_group_name) = UPPER(?)
    """, (group_name,))
    group_row = cursor.fetchone()

    if not group_row:
        raise HTTPException(status_code=404, detail=f"Peer group '{group_name}' not found.")

    exact_group = group_row["peer_group_name"]

    # Fetch latest year percentiles
    query = """
    SELECT 
        pp.company_id,
        c.company_name,
        pp.metric,
        pp.value,
        pp.percentile_rank,
        pp.year
    FROM peer_percentiles pp
    JOIN companies c ON pp.company_id = c.id
    WHERE pp.peer_group_name = ?
      AND pp.year = (SELECT MAX(year) FROM peer_percentiles pp2 WHERE pp2.peer_group_name = pp.peer_group_name)
    ORDER BY pp.company_id, pp.metric
    """
    df = pd.read_sql(query, conn, params=[exact_group])

    if df.empty:
        raise HTTPException(status_code=404, detail=f"No percentile data found for peer group '{exact_group}'.")

    # Pivot into structured company records
    pivoted = df.pivot(index=['company_id', 'company_name', 'year'], columns='metric', values=['value', 'percentile_rank'])
    companies_out = []

    for (cid, cname, yr) in pivoted.index:
        comp_dict = {
            "company_id": cid,
            "company_name": cname,
            "year": yr,
            "metrics": {}
        }
        for col in df['metric'].unique():
            val = pivoted.loc[(cid, cname, yr), ('value', col)]
            rank = pivoted.loc[(cid, cname, yr), ('percentile_rank', col)]
            comp_dict["metrics"][col] = {
                "value": round(float(val), 2) if pd.notna(val) else None,
                "percentile_rank": round(float(rank), 4) if pd.notna(rank) else None
            }
        companies_out.append(comp_dict)

    return {
        "peer_group": exact_group,
        "company_count": len(companies_out),
        "constituents": companies_out
    }


@router.get("/companies/{ticker}/peers/compare")
def compare_company_peers(ticker: str, conn: sqlite3.Connection = Depends(get_db)):
    """Return 8-axis radar comparison data: company values vs peer group average vs benchmark company."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM companies WHERE UPPER(id) = UPPER(?)", (ticker,))
    comp_row = cursor.fetchone()
    if not comp_row:
        raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found.")
    exact_ticker = comp_row["id"]

    # Identify peer group
    cursor.execute("SELECT peer_group_name FROM peer_groups WHERE company_id = ?", (exact_ticker,))
    pg_row = cursor.fetchone()
    if not pg_row:
        # Fallback to broad sector
        cursor.execute("SELECT broad_sector FROM sectors WHERE company_id = ?", (exact_ticker,))
        sec_row = cursor.fetchone()
        peer_group_name = sec_row["broad_sector"] if sec_row else "Unknown"
    else:
        peer_group_name = pg_row["peer_group_name"]

    # Benchmark company for this peer group (or highest market cap)
    cursor.execute("SELECT company_id FROM peer_groups WHERE peer_group_name = ? AND is_benchmark = 1", (peer_group_name,))
    bm_row = cursor.fetchone()
    benchmark_id = bm_row["company_id"] if bm_row else exact_ticker

    # Load latest ratios for all peers in this peer group
    query = """
    SELECT 
        fr.company_id,
        fr.return_on_equity_pct,
        fr.return_on_capital_pct,
        fr.net_profit_margin_pct,
        fr.debt_to_equity,
        fr.free_cash_flow_cr,
        fr.pat_cagr_5yr,
        fr.revenue_cagr_5yr,
        fr.eps_cagr_5yr
    FROM financial_ratios fr
    JOIN peer_groups pg ON fr.company_id = pg.company_id
    WHERE pg.peer_group_name = ?
      AND fr.year = (SELECT MAX(year) FROM financial_ratios fr2 WHERE fr2.company_id = fr.company_id)
    """
    df_peers = pd.read_sql(query, conn, params=[peer_group_name])

    if df_peers.empty:
        # Fallback: query from broad sector if peer group table empty
        query_sec = """
        SELECT 
            fr.company_id,
            fr.return_on_equity_pct,
            fr.return_on_capital_pct,
            fr.net_profit_margin_pct,
            fr.debt_to_equity,
            fr.free_cash_flow_cr,
            fr.pat_cagr_5yr,
            fr.revenue_cagr_5yr,
            fr.eps_cagr_5yr
        FROM financial_ratios fr
        JOIN sectors s ON fr.company_id = s.company_id
        WHERE s.broad_sector = ?
          AND fr.year = (SELECT MAX(year) FROM financial_ratios fr2 WHERE fr2.company_id = fr.company_id)
        """
        df_peers = pd.read_sql(query_sec, conn, params=[peer_group_name])

    company_vals = {}
    benchmark_vals = {}
    peer_avg_vals = {}

    df_comp = df_peers[df_peers['company_id'] == exact_ticker]
    df_bm = df_peers[df_peers['company_id'] == benchmark_id]

    for m in RADAR_METRICS:
        # Company val
        if not df_comp.empty and pd.notna(df_comp[m].iloc[0]):
            company_vals[m] = round(float(df_comp[m].iloc[0]), 2)
        else:
            company_vals[m] = None

        # Benchmark val
        if not df_bm.empty and pd.notna(df_bm[m].iloc[0]):
            benchmark_vals[m] = round(float(df_bm[m].iloc[0]), 2)
        else:
            benchmark_vals[m] = None

        # Peer average
        avg_val = df_peers[m].mean()
        peer_avg_vals[m] = round(float(avg_val), 2) if pd.notna(avg_val) else None

    return {
        "company_id": exact_ticker,
        "peer_group": peer_group_name,
        "benchmark_company": benchmark_id,
        "axis_metrics": RADAR_METRICS,
        "company_values": company_vals,
        "peer_group_averages": peer_avg_vals,
        "benchmark_values": benchmark_vals
    }
