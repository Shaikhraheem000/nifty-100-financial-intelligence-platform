"""
Sector analytics and constituent breakdown router.
"""

from fastapi import APIRouter, Depends, HTTPException
import sqlite3
import pandas as pd
from src.api.db import get_db

router = APIRouter(prefix="/sectors", tags=["Sectors"])


@router.get("")
def list_sectors(conn: sqlite3.Connection = Depends(get_db)):
    """Return all sectors with company count, median ROE, median P/E, and median D/E."""
    query = """
    SELECT 
        s.broad_sector as sector,
        c.id as company_id,
        fr.return_on_equity_pct as roe,
        mc.pe_ratio as pe,
        fr.debt_to_equity as de
    FROM sectors s
    JOIN companies c ON s.company_id = c.id
    LEFT JOIN (
        SELECT fr1.company_id, fr1.return_on_equity_pct, fr1.debt_to_equity
        FROM financial_ratios fr1
        INNER JOIN (
            SELECT company_id, MAX(year) as max_year
            FROM financial_ratios
            GROUP BY company_id
        ) fr2 ON fr1.company_id = fr2.company_id AND fr1.year = fr2.max_year
    ) fr ON c.id = fr.company_id
    LEFT JOIN (
        SELECT mc1.company_id, mc1.pe_ratio
        FROM market_cap mc1
        INNER JOIN (
            SELECT company_id, MAX(year) as max_year
            FROM market_cap
            GROUP BY company_id
        ) mc2 ON mc1.company_id = mc2.company_id AND mc1.year = mc2.max_year
    ) mc ON c.id = mc.company_id
    """
    df = pd.read_sql(query, conn)
    for col in ['roe', 'pe', 'de']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    sectors_list = []
    for sec_name, group in df.groupby('sector'):
        roe_clean = group['roe'].dropna()
        pe_clean = group['pe'].dropna()
        de_clean = group['de'].dropna()

        sectors_list.append({
            "sector": str(sec_name),
            "company_count": len(group),
            "median_roe": round(float(roe_clean.median()), 2) if not roe_clean.empty else None,
            "median_pe": round(float(pe_clean.median()), 2) if not pe_clean.empty else None,
            "median_de": round(float(de_clean.median()), 2) if not de_clean.empty else None
        })

    sectors_list.sort(key=lambda x: x['company_count'], reverse=True)
    return sectors_list


@router.get("/{sector}/companies")
def get_sector_companies(sector: str, conn: sqlite3.Connection = Depends(get_db)):
    """Return all constituent companies within a sector with latest year financial metrics."""
    query = """
    SELECT 
        c.id as company_id,
        c.company_name,
        s.broad_sector,
        s.sub_sector,
        fr.return_on_equity_pct as roe,
        fr.return_on_capital_pct as roce,
        fr.debt_to_equity as de,
        fr.operating_profit_margin_pct as opm,
        fr.revenue_cagr_5yr,
        mc.market_cap_crore,
        mc.pe_ratio
    FROM companies c
    JOIN sectors s ON c.id = s.company_id
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
    WHERE UPPER(s.broad_sector) = UPPER(?) OR UPPER(s.sub_sector) = UPPER(?)
    ORDER BY mc.market_cap_crore DESC
    """
    df = pd.read_sql(query, conn, params=[sector, sector])
    if df.empty:
        raise HTTPException(status_code=404, detail=f"Sector '{sector}' not found or contains no companies.")

    clean_records = []
    for row in df.to_dict(orient='records'):
        clean_row = {}
        for k, v in row.items():
            if pd.isna(v):
                clean_row[k] = None
            else:
                clean_row[k] = v
        clean_records.append(clean_row)

    return {
        "sector": sector,
        "company_count": len(clean_records),
        "companies": clean_records
    }
