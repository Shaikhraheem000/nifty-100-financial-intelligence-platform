import sqlite3
import pandas as pd
import logging
import time
import os
from datetime import datetime
from src.etl.loader import DataLoader
from src.etl.normaliser import normalize_ticker, normalize_year
from src.etl.validator import Validator
from src.etl.deduplicator import Deduplicator

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class ETLPipeline:
    def __init__(self, data_dir: str, db_path: str):
        self.data_dir = data_dir
        self.db_path = db_path
        self.loader = DataLoader(data_dir)
        self.validator = Validator()
        self.deduplicator = Deduplicator()
        self.audit_logs = []
        
    def setup_database(self):
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        with open(schema_path, 'r') as f:
            schema = f.read()
            
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            # Drop tables to recreate them for idempotency
            tables = ['market_cap', 'stock_prices', 'sectors', 'prosandcons', 'documents', 'analysis', 'cashflow', 'balancesheet', 'profitandloss', 'companies']
            for table in tables:
                conn.execute(f"DROP TABLE IF EXISTS {table}")
            conn.executescript(schema)
            logger.info("Database schema recreated successfully.")

    def run(self):
        self.setup_database()
        
        # Datasets ordered by FK dependency
        datasets = [
            'companies', 'profitandloss', 'balancesheet', 'cashflow', 
            'analysis', 'documents', 'prosandcons', 'sectors', 'stock_prices', 'market_cap'
        ]
        
        master_ids = set()
        
        for ds in datasets:
            start_time = time.time()
            logger.info(f"Processing dataset: {ds}")
            
            try:
                df = self.loader.load_dataset(ds)
                rows_in = len(df)
            except Exception as e:
                logger.error(f"Failed to load {ds}: {e}")
                continue
                
            # Normalise
            if 'company_id' in df.columns:
                df['company_id'] = df['company_id'].apply(normalize_ticker)
            if 'id' in df.columns and ds == 'companies':
                df['id'] = df['id'].apply(normalize_ticker)
                
            if 'year' in df.columns and ds in ['profitandloss', 'balancesheet', 'cashflow']:
                df['year'] = df['year'].apply(normalize_year)
            
            # Validate format
            if ds == 'companies':
                df = self.validator.check_ticker_format(df, ds, 'id')
            elif 'company_id' in df.columns:
                df = self.validator.check_ticker_format(df, ds, 'company_id')
                
            if 'year' in df.columns and ds in ['profitandloss', 'balancesheet', 'cashflow']:
                df = self.validator.check_year_format(df, ds)
                
            # Validate PK & FK
            if ds == 'companies':
                if not self.validator.validate_company_pk_uniqueness(df):
                    logger.error("Halt load: duplicate company PK")
                    break
                master_ids = set(df['id'].unique())
            else:
                if 'company_id' in df.columns:
                    df = self.validator.validate_fk_integrity(df, master_ids, ds)
            
            # Data-specific validation
            if ds == 'balancesheet':
                df = self.validator.check_balance_sheet(df)
            elif ds == 'profitandloss':
                df = self.validator.check_profit_and_loss(df, pd.DataFrame()) # Mock companies for now
            elif ds == 'cashflow':
                df = self.validator.check_cashflow(df)
            elif ds == 'documents':
                df = self.validator.check_url_validity(df)
                
            # Deduplicate
            if ds in ['profitandloss', 'balancesheet', 'cashflow', 'market_cap']:
                df = self.deduplicator.deduplicate(df, ['company_id', 'year'], ds)
            elif ds == 'stock_prices':
                df = self.deduplicator.deduplicate(df, ['company_id', 'date'], ds)
            elif ds == 'documents':
                df = self.deduplicator.deduplicate(df, ['company_id', 'year'], ds)
            elif ds in ['analysis', 'sectors']:
                df = self.deduplicator.deduplicate(df, ['company_id'], ds)
                
            # Drop temporary lineage columns before insert
            if '_source_file' in df.columns:
                df = df.drop(columns=['_source_file'])
            if '_ingested_at' in df.columns:
                df = df.drop(columns=['_ingested_at'])
                
            # Insert to DB
            rows_out = len(df)
            rejected = rows_in - rows_out
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON;")
                df.to_sql(ds, conn, if_exists='append', index=False)
                
            runtime_s = time.time() - start_time
            self.audit_logs.append({
                'table': ds,
                'rows_in': rows_in,
                'rows_out': rows_out,
                'rejected': rejected,
                'timestamp': datetime.now().isoformat(),
                'runtime_s': runtime_s
            })
            
        # Global validation
        with sqlite3.connect(self.db_path) as conn:
            pl_df = pd.read_sql("SELECT * FROM profitandloss", conn)
            bs_df = pd.read_sql("SELECT * FROM balancesheet", conn)
            cf_df = pd.read_sql("SELECT * FROM cashflow", conn)
            self.validator.check_coverage(pl_df, bs_df, cf_df)

        # Output audit files
        audit_df = pd.DataFrame(self.audit_logs)
        audit_df.to_csv(os.path.join(self.data_dir, '..', 'output', 'load_audit.csv'), index=False)
        
        failures_df = self.validator.get_failures_df()
        failures_df.to_csv(os.path.join(self.data_dir, '..', 'output', 'validation_failures.csv'), index=False)
        
        # Deduplication logs could also be outputted if needed, but not strictly requested as a separate file.
        # But we log them.

if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    data_dir = os.path.join(base_dir, 'data')
    db_path = os.path.join(data_dir, 'nifty100.db')
    
    pipeline = ETLPipeline(data_dir, db_path)
    pipeline.run()
