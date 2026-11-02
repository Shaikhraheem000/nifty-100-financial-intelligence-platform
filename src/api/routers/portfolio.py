"""
Portfolio statistics and market distribution router.
"""

import os
from fastapi import APIRouter
import pandas as pd
from src.api.db import BASE_DIR

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


@router.get("/stats")
def get_portfolio_stats():
    """Return P10 through P90 distribution percentiles, Mean, and Standard Deviation for 10 core KPIs across all 92 companies."""
    stats_file = os.path.join(BASE_DIR, 'output', 'portfolio_stats.csv')
    if os.path.exists(stats_file):
        df = pd.read_csv(stats_file)
        return {
            "universe_size": 92,
            "metrics_count": len(df),
            "statistics": df.to_dict(orient="records")
        }

    # If file not present yet, return empty list
    return {
        "universe_size": 92,
        "metrics_count": 0,
        "statistics": []
    }
