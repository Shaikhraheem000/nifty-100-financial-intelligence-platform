"""
Health check and database telemetry router.
"""

import time
from fastapi import APIRouter, Depends
import sqlite3
from src.api.db import get_db

router = APIRouter(tags=["Health"])
START_TIME = time.time()

TABLES_TO_CHECK = [
    "companies",
    "profitandloss",
    "balancesheet",
    "cashflow",
    "analysis",
    "documents",
    "prosandcons",
    "sectors",
    "stock_prices",
    "market_cap"
]


@router.get("/health")
def get_health(conn: sqlite3.Connection = Depends(get_db)):
    """Return platform operational status, version, uptime, and database row counts for all 10 core tables."""
    cursor = conn.cursor()
    row_counts = {}
    for table in TABLES_TO_CHECK:
        try:
            cursor.execute(f"SELECT COUNT(*) as cnt FROM {table}")
            res = cursor.fetchone()
            row_counts[table] = res["cnt"] if res else 0
        except Exception:
            row_counts[table] = 0

    uptime = round(time.time() - START_TIME, 2)

    return {
        "status": "ok",
        "version": "1.0.0",
        "uptime_seconds": uptime,
        "db_row_counts": row_counts
    }
