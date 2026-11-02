"""
Company analytics, financial statements, and tearsheet report router.
"""

import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
import sqlite3
from src.api.db import get_db, BASE_DIR

router = APIRouter(prefix="/companies", tags=["Companies"])


def check_company_exists(ticker: str, conn: sqlite3.Connection):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM companies WHERE UPPER(id) = UPPER(?)", (ticker,))
    res = cursor.fetchone()
    if not res:
        raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found.")
    return res["id"]


@router.get("")
def list_companies(
    sector: Optional[str] = Query(None, description="Filter by broad sector name"),
    market_cap_category: Optional[str] = Query(None, description="Filter by market cap category (e.g. Large Cap)"),
    search: Optional[str] = Query(None, description="Search term for company ticker or name"),
    conn: sqlite3.Connection = Depends(get_db)
):
    """Return all companies matching search, sector, or market cap criteria with core profitability ratios."""
    cursor = conn.cursor()
    query = """
    SELECT 
        c.id,
        c.company_name,
        s.market_cap_category,
        s.broad_sector,
        s.sub_sector,
        fr.return_on_equity_pct as roe_pct,
        fr.return_on_capital_pct as roce_pct
    FROM companies c
    LEFT JOIN sectors s ON c.id = s.company_id
    LEFT JOIN (
        SELECT fr1.company_id, fr1.return_on_equity_pct, fr1.return_on_capital_pct
        FROM financial_ratios fr1
        INNER JOIN (
            SELECT company_id, MAX(year) as max_year
            FROM financial_ratios
            GROUP BY company_id
        ) fr2 ON fr1.company_id = fr2.company_id AND fr1.year = fr2.max_year
    ) fr ON c.id = fr.company_id
    WHERE 1=1
    """
    params = []
    if sector:
        query += " AND UPPER(s.broad_sector) = UPPER(?)"
        params.append(sector)
    if market_cap_category:
        query += " AND UPPER(s.market_cap_category) = UPPER(?)"
        params.append(market_cap_category)
    if search:
        query += " AND (UPPER(c.id) LIKE UPPER(?) OR UPPER(c.company_name) LIKE UPPER(?))"
        pattern = f"%{search}%"
        params.extend([pattern, pattern])

    query += " ORDER BY c.id ASC"
    cursor.execute(query, params)
    return [dict(r) for r in cursor.fetchall()]


@router.get("/{ticker}")
def get_company_profile(ticker: str, conn: sqlite3.Connection = Depends(get_db)):
    """Return comprehensive company profile, sector classification, and latest financial indicators."""
    exact_ticker = check_company_exists(ticker, conn)
    cursor = conn.cursor()

    # Company info
    cursor.execute("SELECT * FROM companies WHERE id = ?", (exact_ticker,))
    company = cursor.fetchone()

    # Sector info
    cursor.execute("SELECT broad_sector, sub_sector FROM sectors WHERE company_id = ?", (exact_ticker,))
    sec = cursor.fetchone()

    # Latest ratios
    cursor.execute("""
        SELECT * FROM financial_ratios 
        WHERE company_id = ? 
        ORDER BY year DESC LIMIT 1
    """, (exact_ticker,))
    latest_ratios = cursor.fetchone()

    # Latest market cap & valuation multiples
    cursor.execute("""
        SELECT * FROM market_cap 
        WHERE company_id = ? 
        ORDER BY year DESC LIMIT 1
    """, (exact_ticker,))
    latest_mc = cursor.fetchone()

    profile = dict(company)
    profile["sector"] = sec["broad_sector"] if sec else None
    profile["sub_sector"] = sec["sub_sector"] if sec else None
    profile["latest_ratios"] = dict(latest_ratios) if latest_ratios else {}
    profile["latest_valuation"] = dict(latest_mc) if latest_mc else {}

    return profile


@router.get("/{ticker}/pl")
def get_company_pl(
    ticker: str,
    from_year: Optional[str] = Query(None, description="Start year filter (YYYY or YYYY-MM)"),
    to_year: Optional[str] = Query(None, description="End year filter (YYYY or YYYY-MM)"),
    conn: sqlite3.Connection = Depends(get_db)
):
    """Return historical Profit and Loss statements for the company."""
    exact_ticker = check_company_exists(ticker, conn)
    cursor = conn.cursor()
    query = "SELECT * FROM profitandloss WHERE company_id = ?"
    params = [exact_ticker]

    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)

    query += " ORDER BY year ASC"
    cursor.execute(query, params)
    return [dict(r) for r in cursor.fetchall()]


@router.get("/{ticker}/bs")
def get_company_bs(
    ticker: str,
    from_year: Optional[str] = Query(None, description="Start year filter (YYYY or YYYY-MM)"),
    to_year: Optional[str] = Query(None, description="End year filter (YYYY or YYYY-MM)"),
    conn: sqlite3.Connection = Depends(get_db)
):
    """Return historical Balance Sheet statements for the company."""
    exact_ticker = check_company_exists(ticker, conn)
    cursor = conn.cursor()
    query = "SELECT * FROM balancesheet WHERE company_id = ?"
    params = [exact_ticker]

    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)

    query += " ORDER BY year ASC"
    cursor.execute(query, params)
    return [dict(r) for r in cursor.fetchall()]


@router.get("/{ticker}/cashflow")
def get_company_cashflow(
    ticker: str,
    from_year: Optional[str] = Query(None, description="Start year filter (YYYY or YYYY-MM)"),
    to_year: Optional[str] = Query(None, description="End year filter (YYYY or YYYY-MM)"),
    conn: sqlite3.Connection = Depends(get_db)
):
    """Return historical Cash Flow statements for the company."""
    exact_ticker = check_company_exists(ticker, conn)
    cursor = conn.cursor()
    query = "SELECT * FROM cashflow WHERE company_id = ?"
    params = [exact_ticker]

    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)

    query += " ORDER BY year ASC"
    cursor.execute(query, params)
    return [dict(r) for r in cursor.fetchall()]


@router.get("/{ticker}/ratios")
def get_company_ratios(
    ticker: str,
    year: Optional[str] = Query(None, description="Specific year filter (e.g. 2024 or 2024-03)"),
    conn: sqlite3.Connection = Depends(get_db)
):
    """Return computed financial KPIs and ratios across historical periods."""
    exact_ticker = check_company_exists(ticker, conn)
    cursor = conn.cursor()
    query = "SELECT * FROM financial_ratios WHERE company_id = ?"
    params = [exact_ticker]

    if year:
        query += " AND year LIKE ?"
        params.append(f"{year[:4]}%")

    query += " ORDER BY year ASC"
    cursor.execute(query, params)
    return [dict(r) for r in cursor.fetchall()]


@router.get("/{ticker}/tearsheet")
def download_company_tearsheet(ticker: str, conn: sqlite3.Connection = Depends(get_db)):
    """Download the pre-generated 2-page executive tearsheet PDF for the company."""
    exact_ticker = check_company_exists(ticker, conn)
    pdf_path = os.path.join(BASE_DIR, 'reports', 'tearsheets', f"{exact_ticker}_tearsheet.pdf")

    if not os.path.exists(pdf_path):
        raise HTTPException(
            status_code=404,
            detail=f"Tearsheet PDF for company '{exact_ticker}' not found on disk."
        )

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"{exact_ticker}_tearsheet.pdf"
    )
