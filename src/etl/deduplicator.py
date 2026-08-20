import pandas as pd
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class Deduplicator:
    def __init__(self):
        self.logs = []

    def deduplicate(self, df: pd.DataFrame, subset: list, dataset_name: str) -> pd.DataFrame:
        if df.empty:
            return df
            
        # Find duplicates
        is_dup = df.duplicated(subset=subset, keep=False)
        duplicates = df[is_dup]
        
        if duplicates.empty:
            return df
            
        # Deterministically keep last occurrence (sort first to be fully deterministic if needed, 
        # but keep='last' on the original order is deterministic)
        df_clean = df.drop_duplicates(subset=subset, keep='last').copy()
        
        # Log deduplication
        dup_groups = duplicates.groupby(subset)
        for name, group in dup_groups:
            if isinstance(name, tuple):
                keys = dict(zip(subset, name))
            else:
                keys = {subset[0]: name}
                
            self.logs.append({
                'dataset': dataset_name,
                'company_id': keys.get('company_id', 'N/A'),
                'year': keys.get('year', 'N/A'),
                'number_of_duplicates': len(group),
                'retained_record_index': group.index[-1],
                'reason': 'Kept last occurrence'
            })
            
        logger.info(f"Deduplicated {len(duplicates) - len(dup_groups)} rows in {dataset_name}")
        return df_clean

    def get_logs_df(self) -> pd.DataFrame:
        if not self.logs:
            return pd.DataFrame(columns=['dataset', 'company_id', 'year', 'number_of_duplicates', 'retained_record_index', 'reason'])
        return pd.DataFrame(self.logs)
