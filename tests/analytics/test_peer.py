import pytest
import os
import sqlite3
import pandas as pd
from src.analytics.peer import PeerEngine

def test_peer_engine():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    db_path = os.path.join(base_dir, 'data', 'nifty100.db')
    
    engine = PeerEngine(db_path)
    engine.load_data()
    engine.compute_percentiles()
    
    pdf = engine.percentiles_df
    
    # 1. Check inversion of D/E
    # D/E is lower_is_better. So the company with the lowest D/E should have the highest percentile
    # Let's take IT Services as an example
    it_de = pdf[(pdf['peer_group_name'] == 'IT Services') & (pdf['metric'] == 'debt_to_equity')]
    if not it_de.empty:
        # Find company with lowest D/E in the raw df
        raw_it = engine.df[(engine.df['peer_group_name'] == 'IT Services')]
        year = it_de['year'].iloc[0]
        raw_it_year = raw_it[raw_it['year'] == year].dropna(subset=['debt_to_equity'])
        
        if not raw_it_year.empty:
            lowest_de_company = raw_it_year.loc[raw_it_year['debt_to_equity'].idxmin()]['company_id']
            # Find its rank
            rank = it_de[it_de['company_id'] == lowest_de_company]['percentile_rank'].iloc[0]
            max_rank_in_group = it_de['percentile_rank'].max()
            assert rank == max_rank_in_group
            
    # 2. Check ROE
    it_roe = pdf[(pdf['peer_group_name'] == 'IT Services') & (pdf['metric'] == 'return_on_equity_pct')]
    if not it_roe.empty:
        raw_it = engine.df[(engine.df['peer_group_name'] == 'IT Services')]
        year = it_roe['year'].iloc[0]
        raw_it_year = raw_it[raw_it['year'] == year].dropna(subset=['return_on_equity_pct'])
        
        if not raw_it_year.empty:
            highest_roe_company = raw_it_year.loc[raw_it_year['return_on_equity_pct'].idxmax()]['company_id']
            rank = it_roe[it_roe['company_id'] == highest_roe_company]['percentile_rank'].iloc[0]
            max_rank_roe = it_roe['percentile_rank'].max()
            assert rank == max_rank_roe
            
    # 3. Missing peer group handled
    # Any company with no peer group should not be in the percentiles df
    unassigned = engine.df[engine.df['peer_group_name'].isna()]
    if not unassigned.empty:
        unassigned_ids = unassigned['company_id'].unique()
        for cid in unassigned_ids:
            assert cid not in pdf['company_id'].values
