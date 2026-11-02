"""
Annual reports and regulatory filings router.
"""

from fastapi import APIRouter, Depends, HTTPException
import sqlite3
import pandas as pd
from src.api.db import get_db

router = APIRouter(tags=["Documents"])


@router.get("/companies/{ticker}/documents")
def get_company_documents(ticker: str, conn: sqlite3.Connection = Depends(get_db)):
    """Return annual report regulatory filing links with URL validity status for the company."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM companies WHERE UPPER(id) = UPPER(?)", (ticker,))
    comp_row = cursor.fetchone()
    if not comp_row:
        raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found.")
    exact_ticker = comp_row["id"]

    cursor.execute("""
        SELECT year, annual_report
        FROM documents
        WHERE company_id = ?
        ORDER BY year DESC
    """, (exact_ticker,))
    rows = cursor.fetchall()

    documents = []
    for r in rows:
        url = r["annual_report"]
        yr = r["year"]
        is_valid = bool(url and pd.notna(url) and str(url).startswith("http"))
        documents.append({
            "year": yr,
            "bse_url": url,
            "is_url_valid": is_valid
        })

    return {
        "company_id": exact_ticker,
        "document_count": len(documents),
        "documents": documents
    }
