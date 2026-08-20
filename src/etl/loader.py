import os
import hashlib
import pandas as pd
import logging
from datetime import datetime
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

DATASETS_CONFIG = {
    "companies": {"filename": "companies.xlsx", "dir": "raw", "header": 1, "target_table": "companies"},
    "profitandloss": {"filename": "profitandloss.xlsx", "dir": "raw", "header": 1, "target_table": "profitandloss"},
    "balancesheet": {"filename": "balancesheet.xlsx", "dir": "raw", "header": 1, "target_table": "balancesheet"},
    "cashflow": {"filename": "cashflow.xlsx", "dir": "raw", "header": 1, "target_table": "cashflow"},
    "analysis": {"filename": "analysis.xlsx", "dir": "raw", "header": 1, "target_table": "analysis"},
    "documents": {"filename": "documents.xlsx", "dir": "raw", "header": 1, "target_table": "documents"},
    "prosandcons": {"filename": "prosandcons.xlsx", "dir": "raw", "header": 1, "target_table": "prosandcons"},
    
    "sectors": {"filename": "sectors.xlsx", "dir": "supporting", "header": 0, "target_table": "sectors"},
    "stock_prices": {"filename": "stock_prices.xlsx", "dir": "supporting", "header": 0, "target_table": "stock_prices"},
    "market_cap": {"filename": "market_cap.xlsx", "dir": "supporting", "header": 0, "target_table": "market_cap"},
    "financial_ratios": {"filename": "financial_ratios.xlsx", "dir": "supporting", "header": 0, "target_table": "financial_ratios"},
    "peer_groups": {"filename": "peer_groups.xlsx", "dir": "supporting", "header": 0, "target_table": "peer_groups"},
}

class DataLoader:
    def __init__(self, base_data_dir: str):
        self.base_data_dir = base_data_dir
        self.manifest = []

    def compute_file_manifest(self, filepath: str, dataset_name: str, row_count: int):
        if not os.path.exists(filepath):
            return
            
        file_size = os.path.getsize(filepath)
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
                
        self.manifest.append({
            "dataset": dataset_name,
            "filename": os.path.basename(filepath),
            "file_size": file_size,
            "sha256": sha256.hexdigest(),
            "row_count": row_count,
            "ingestion_timestamp": datetime.now().isoformat()
        })

    def load_dataset(self, dataset_name: str) -> pd.DataFrame:
        if dataset_name not in DATASETS_CONFIG:
            raise ValueError(f"Unknown dataset: {dataset_name}")
            
        config = DATASETS_CONFIG[dataset_name]
        filepath = os.path.join(self.base_data_dir, config["dir"], config["filename"])
        
        if not os.path.exists(filepath):
            logger.error(f"Missing source file: {filepath}")
            raise FileNotFoundError(f"Missing required source dataset file: {filepath}")
            
        try:
            df = pd.read_excel(filepath, header=config["header"])
            # Strip whitespace from column names and lowercase them
            df.columns = [str(c).strip().replace(' ', '_').lower() for c in df.columns]
            
            # Record manifest
            self.compute_file_manifest(filepath, dataset_name, len(df))
            
            # Lineage
            df['_source_file'] = config["filename"]
            df['_ingested_at'] = datetime.now().isoformat()
            
            logger.info(f"Loaded {dataset_name}: {len(df)} rows")
            return df
            
        except Exception as e:
            logger.error(f"Error loading {dataset_name} from {filepath}: {e}")
            raise

    def get_manifest_df(self) -> pd.DataFrame:
        return pd.DataFrame(self.manifest)
