import re
import pandas as pd
from typing import Any

def normalize_ticker(ticker: Any) -> str:
    if pd.isna(ticker):
        return "MISSING"
    ticker_str = str(ticker).strip().upper()
    if not ticker_str:
        return "MISSING"
    return ticker_str

MONTH_MAP = {
    'JAN': '01', 'JANUARY': '01',
    'FEB': '02', 'FEBRUARY': '02',
    'MAR': '03', 'MARCH': '03',
    'APR': '04', 'APRIL': '04',
    'MAY': '05',
    'JUN': '06', 'JUNE': '06',
    'JUL': '07', 'JULY': '07',
    'AUG': '08', 'AUGUST': '08',
    'SEP': '09', 'SEPTEMBER': '09',
    'OCT': '10', 'OCTOBER': '10',
    'NOV': '11', 'NOVEMBER': '11',
    'DEC': '12', 'DECEMBER': '12'
}

def normalize_year(year_val: Any) -> str:
    if pd.isna(year_val):
        return "PARSE_ERROR"
    
    val = str(year_val).strip()
    
    # Already normalized: YYYY-MM
    if re.match(r'^\d{4}-\d{2}$', val):
        return val
    
    # FY prefix: FY23 -> 2023-03
    m_fy = re.match(r'^FY(\d{2})$', val, re.IGNORECASE)
    if m_fy:
        yy = int(m_fy.group(1))
        yyyy = 2000 + yy if yy < 50 else 1900 + yy
        return f"{yyyy}-03"
    
    # Integer/String year: 2023 -> 2023-03
    m_yr = re.match(r'^(\d{4})$', val)
    if m_yr:
        return f"{m_yr.group(1)}-03"
    
    # Month-Year formats: Mar-23, Mar 23, March-2023, Dec-22, Jun-23
    m_my = re.match(r'^([a-zA-Z]+)[-\s]+(\d{2,4})$', val)
    if m_my:
        month_str = m_my.group(1).upper()
        year_str = m_my.group(2)
        
        if month_str not in MONTH_MAP:
            return "PARSE_ERROR"
            
        month = MONTH_MAP[month_str]
        
        if len(year_str) == 2:
            yy = int(year_str)
            yyyy = 2000 + yy if yy < 50 else 1900 + yy
        else:
            yyyy = int(year_str)
            
        return f"{yyyy}-{month}"
        
    return "PARSE_ERROR"
