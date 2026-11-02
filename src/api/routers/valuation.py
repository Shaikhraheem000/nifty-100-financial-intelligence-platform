"""
Historical valuation multiples and market capitalization router.
"""

from fastapi import APIRouter, Depends, HTTPException
import sqlite3
from src.api.db import get_db

router = APIRouter(prefix="/market-cap", tags=["Valuation"])


@router.get("/{ticker}")
def get_valuation_multiples(ticker: str, conn: sqlite3.Connection = Depends(get_db)):
    """Return historical valuation multiples (P/E, P/B, EV/EBITDA, Dividend Yield) from 2019 to 2024."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM companies WHERE UPPER(id) = UPPER(?)", (ticker,))
    comp_row = cursor.fetchone()
    if not comp_row:
        raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found.")
    exact_ticker = comp_row["id"]

    cursor.execute("""
        SELECT 
            year,
            market_cap_crore,
            enterprise_value_crore,
            pe_ratio,
            pb_ratio,
            ev_ebitda,
            dividend_yield_pct
        FROM market_cap
        WHERE company_id = ?
        ORDER BY year ASC
    """, (exact_ticker,))
    rows = cursor.fetchall()

    return {
        "company_id": exact_ticker,
        "history_count": len(rows),
        "multiples": [dict(r) for r in rows]
    }
