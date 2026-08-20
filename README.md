# Nifty 100 Financial Intelligence Platform

## Project Overview
The Nifty 100 Financial Intelligence Platform transforms raw financial statement data into structured analytics intelligence for 92 Nifty 100 companies. This repository currently contains the **Sprint 1** release: Data Foundation & ETL Pipeline.

## Sprint 1 Architecture
Sprint 1 implements a production-grade Extract, Transform, Load (ETL) pipeline that:
1. Ingests 7 core and 5 supplementary raw Excel datasets.
2. Normalises company tickers and financial year representations.
3. Validates against 16 data quality rules (logging CRITICAL and WARNING).
4. Deduplicates deterministically on time-series datasets.
5. Loads data into a 10-table SQLite database (`nifty100.db`).
6. Enforces referential integrity (foreign keys) and guarantees idempotency.

## Setup Instructions
1. Navigate to the project directory:
   ```bash
   cd "C:\Users\shaikh raheem\OneDrive\Desktop\N100 FINANCIAL INTELLIGENCE PLATFORM\nifty100_platform"
   ```
2. Set up the virtual environment (optional but recommended):
   ```bash
   python -m venv .venv
   # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   make install
   # Or manually: pip install -r requirements.txt
   ```
4. Configure environment variables (copy `.env.template` to `.env`).

## ETL Execution
To run the full ETL pipeline and build the database:
```bash
make load
# Or manually: python -m src.etl.db_loader
```
The resulting database will be located at:
`data/nifty100.db`

## Test Execution
To run the pytest suite:
```bash
make test
# Or manually: python -m pytest tests/ -v
```

## Audit and Data Quality Outputs
After the ETL runs, audit logs and validation outputs are generated in the `output/` directory:
- `output/load_audit.csv`: Row counts in, out, rejected, and runtimes.
- `output/validation_failures.csv`: Log of data quality rule violations (CRITICAL / WARNING / INFO).

## Known Limitations (Sprint 1)
- `face_value` in the `companies` dataset contains nulls, therefore the `NOT NULL` constraint was removed.
- `operating_profit` and `opm_percentage` contained nulls in raw source, necessitating schema relaxation to allow 100% data ingestion.
- The Ratio Engine (Sprint 2) is not yet implemented.

## Sprint 1 Status
**Complete**. The database successfully hosts 92 companies across all 10 tables, passes FK checks, and is ready for Sprint 2.
