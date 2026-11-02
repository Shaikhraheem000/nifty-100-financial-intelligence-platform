"""
Financial Screener REST API router with custom threshold filtering and business logic.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
import sqlite3
import pandas as pd
import numpy as np
from src.api.db import get_db

router = APIRouter(prefix="/screener", tags=["Screener"])


@router.get("")
def screen_companies(
    min_roe: Optional[float] = Query(None, description="Minimum Return on Equity (%)"),
    max_de: Optional[float] = Query(None, description="Maximum Debt to Equity ratio"),
    min_fcf: Optional[float] = Query(None, description="Minimum Free Cash Flow (₹ Cr)"),
    sector: Optional[str] = Query(None, description="Broad sector filter"),
    min_rev_cagr_5yr: Optional[float] = Query(None, description="Minimum 5-year Revenue CAGR (%)"),
    min_pat_cagr_5yr: Optional[float] = Query(None, description="Minimum 5-year PAT CAGR (%)"),
    max_pe: Optional[float] = Query(None, description="Maximum Price-to-Earnings multiple"),
    conn: sqlite3.Connection = Depends(get_db)
):
    """Filter the 92-company universe using customizable fundamental thresholds and return ranked candidates."""
    # Parameter validation
    if min_roe is not None and (min_roe < -100 or min_roe > 1000):
        raise HTTPException(status_code=400, detail="min_roe must be between -100 and 1000.")
    if max_de is not None and max_de < 0:
        raise HTTPException(status_code=400, detail="max_de cannot be negative.")
    if max_pe is not None and max_pe < 0:
        raise HTTPException(status_code=400, detail="max_pe cannot be negative.")
    if min_rev_cagr_5yr is not None and min_rev_cagr_5yr < -100:
        raise HTTPException(status_code=400, detail="min_rev_cagr_5yr cannot be less than -100%.")

    # Load latest company financials
    query = """
    SELECT 
        c.id as company_id,
        c.company_name,
        s.broad_sector,
        s.sub_sector,
        fr.return_on_equity_pct as roe,
        fr.debt_to_equity as de,
        fr.free_cash_flow_cr as fcf,
        fr.revenue_cagr_5yr as rev_cagr_5yr,
        fr.pat_cagr_5yr as pat_cagr_5yr,
        fr.operating_profit_margin_pct as opm,
        mc.pe_ratio as pe,
        mc.market_cap_crore
    FROM companies c
    LEFT JOIN sectors s ON c.id = s.company_id
    LEFT JOIN (
        SELECT fr1.*
        FROM financial_ratios fr1
        INNER JOIN (
            SELECT company_id, MAX(year) as max_year
            FROM financial_ratios
            GROUP BY company_id
        ) fr2 ON fr1.company_id = fr2.company_id AND fr1.year = fr2.max_year
    ) fr ON c.id = fr.company_id
    LEFT JOIN (
        SELECT mc1.*
        FROM market_cap mc1
        INNER JOIN (
            SELECT company_id, MAX(year) as max_year
            FROM market_cap
            GROUP BY company_id
        ) mc2 ON mc1.company_id = mc2.company_id AND mc1.year = mc2.max_year
    ) mc ON c.id = mc.company_id
    """
    df = pd.read_sql(query, conn)

    # Cast numeric columns
    numeric_cols = ['roe', 'de', 'fcf', 'rev_cagr_5yr', 'pat_cagr_5yr', 'opm', 'pe', 'market_cap_crore']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df['broad_sector'] = df['broad_sector'].fillna('').astype(str)

    # Apply filters
    if sector:
        df = df[df['broad_sector'].str.strip().str.upper() == sector.strip().upper()]

    if min_roe is not None:
        df = df[df['roe'].notna() & (df['roe'] >= float(min_roe))]

    if max_de is not None:
        # Per specification: D/E filter skips Financials sector automatically
        non_fin = df['broad_sector'].str.upper() != 'FINANCIALS'
        passes_de = df['de'].fillna(999) <= float(max_de)
        df = df[(~non_fin) | passes_de]

    if min_fcf is not None:
        df = df[df['fcf'].notna() & (df['fcf'] >= float(min_fcf))]

    if min_rev_cagr_5yr is not None:
        df = df[df['rev_cagr_5yr'].notna() & (df['rev_cagr_5yr'] >= float(min_rev_cagr_5yr))]

    if min_pat_cagr_5yr is not None:
        df = df[df['pat_cagr_5yr'].notna() & (df['pat_cagr_5yr'] >= float(min_pat_cagr_5yr))]

    if max_pe is not None:
        df = df[df['pe'].notna() & (df['pe'] > 0) & (df['pe'] <= float(max_pe))]

    # Sort by Market Cap descending
    df = df.sort_values(by='market_cap_crore', ascending=False)
    
    # Replace NaN / inf with None for valid JSON serialization
    clean_records = []
    for row in df.to_dict(orient='records'):
        clean_row = {}
        for k, v in row.items():
            if pd.isna(v) or v is np.nan:
                clean_row[k] = None
            else:
                clean_row[k] = v
        clean_records.append(clean_row)

    return {
        "count": len(clean_records),
        "results": clean_records
    }
