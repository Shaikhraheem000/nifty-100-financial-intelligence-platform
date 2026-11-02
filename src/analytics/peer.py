import pandas as pd
import sqlite3
import os
import matplotlib.pyplot as plt
import numpy as np

class PeerEngine:
    def __init__(self, db_path: str):
        self.db_path = db_path
        
    def load_data(self):
        with sqlite3.connect(self.db_path) as conn:
            self.ratios = pd.read_sql("SELECT * FROM financial_ratios", conn)
            # Fetch peer groups from SQLite or CSV
            try:
                self.peers = pd.read_sql("SELECT company_id, peer_group_name FROM peer_groups", conn)
            except Exception:
                # If not in SQLite, load from raw excel
                base_dir = os.path.dirname(os.path.dirname(self.db_path))
                excel_path = os.path.join(base_dir, 'data', 'supporting', 'peer_groups.xlsx')
                if os.path.exists(excel_path):
                    self.peers = pd.read_excel(excel_path)
                    self.peers.rename(columns={'Symbol': 'company_id', 'Peer Group': 'peer_group_name'}, inplace=True)
                    self.peers.to_sql('peer_groups', conn, index=False)
                else:
                    self.peers = pd.DataFrame(columns=['company_id', 'peer_group_name'])
                    
            companies = pd.read_sql("SELECT id as company_id, company_name FROM companies", conn)
            self.df = self.ratios.merge(self.peers, on='company_id', how='left').merge(companies, on='company_id', how='left')
            self.df['year_dt'] = pd.to_datetime(self.df['year'])
            
    def compute_percentiles(self):
        # 10 metrics: ROE, ROCE, NPM, D/E, FCF, PAT CAGR 5Y, Revenue CAGR 5Y, EPS CAGR 5Y, ICR, Asset Turnover
        metrics = {
            'return_on_equity_pct': True,
            'return_on_capital_pct': True,
            'net_profit_margin_pct': True,
            'debt_to_equity': False, # Inverse
            'free_cash_flow_cr': True,
            'pat_cagr_5yr': True,
            'revenue_cagr_5yr': True,
            'eps_cagr_5yr': True,
            'interest_coverage': True,
            'asset_turnover': True
        }
        
        percentiles = []
        
        for (group, year), group_df in self.df.groupby(['peer_group_name', 'year']):
            for metric, higher_better in metrics.items():
                if metric not in group_df.columns:
                    continue
                    
                valid = group_df.dropna(subset=[metric])
                if len(valid) == 0:
                    continue
                    
                if len(valid) == 1:
                    ranks = pd.Series([1.0], index=valid.index)
                else:
                    # SQL PERCENT_RANK: (rank - 1) / (N - 1) using max method for ties to give best score
                    raw_ranks = valid[metric].rank(method='max', ascending=True)
                    ranks = (raw_ranks - 1) / (len(valid) - 1)
                    
                if not higher_better:
                    raw_ranks = valid[metric].rank(method='max', ascending=False)
                    ranks = (raw_ranks - 1) / (len(valid) - 1) if len(valid) > 1 else pd.Series([1.0], index=valid.index)
                    
                for idx, row in valid.iterrows():
                    percentiles.append({
                        'company_id': row['company_id'],
                        'peer_group_name': group,
                        'metric': metric,
                        'value': row[metric],
                        'percentile_rank': ranks.loc[idx],
                        'year': year
                    })
                    
        self.percentiles_df = pd.DataFrame(percentiles)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            # To be idempotent, create table and delete existing
            conn.execute('''CREATE TABLE IF NOT EXISTS peer_percentiles (
                            company_id VARCHAR,
                            peer_group_name VARCHAR,
                            metric VARCHAR,
                            value NUMERIC,
                            percentile_rank NUMERIC,
                            year VARCHAR
                        )''')
            conn.execute("DELETE FROM peer_percentiles")
            self.percentiles_df.to_sql('peer_percentiles', conn, if_exists='append', index=False)
            
    def generate_excel(self, output_path: str):
        # Get latest year
        idx = self.df.groupby('company_id')['year_dt'].idxmax()
        latest = self.df.loc[idx].copy()
        
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            workbook = writer.book
            
            green_fmt = workbook.add_format({'bg_color': '#C6EFCE'})
            yellow_fmt = workbook.add_format({'bg_color': '#FFEB9C'})
            red_fmt = workbook.add_format({'bg_color': '#FFC7CE'})
            gold_fmt = workbook.add_format({'bg_color': '#FFD700', 'bold': True})
            
            for group_name, group_df in latest.groupby('peer_group_name'):
                sheet_name = str(group_name)[:31].replace('/', '_')
                
                # Fetch percentiles for this group for latest year
                year = group_df['year'].iloc[0]
                p_df = self.percentiles_df[(self.percentiles_df['peer_group_name'] == group_name) & (self.percentiles_df['year'] == year)]
                
                # Pivot percentiles
                if not p_df.empty:
                    p_pivot = p_df.pivot(index='company_id', columns='metric', values='percentile_rank')
                    p_pivot.columns = [f"{c}_prank" for c in p_pivot.columns]
                    group_df = group_df.merge(p_pivot, on='company_id', how='left')
                
                # Calculate Best-in-Class (>=0.75 for >=6 metrics) and Watch List (<=0.25 for >=4 metrics)
                prank_cols = [c for c in group_df.columns if c.endswith('_prank')]
                group_df['best_in_class'] = (group_df[prank_cols] >= 0.75).sum(axis=1) >= 6
                group_df['watch_list'] = (group_df[prank_cols] <= 0.25).sum(axis=1) >= 4
                
                group_df.to_excel(writer, sheet_name=sheet_name, index=False)
                worksheet = writer.sheets[sheet_name]
                
                # Format percentile columns
                for c_idx, col_name in enumerate(group_df.columns):
                    if col_name.endswith('_prank'):
                        col_letter = chr(65 + c_idx)
                        if c_idx > 25:
                            col_letter = chr(64 + c_idx // 26) + chr(65 + c_idx % 26)
                        
                        worksheet.conditional_format(f"{col_letter}2:{col_letter}100", {'type': 'cell', 'criteria': '>=', 'value': 0.75, 'format': green_fmt})
                        worksheet.conditional_format(f"{col_letter}2:{col_letter}100", {'type': 'cell', 'criteria': 'between', 'minimum': 0.25, 'maximum': 0.749, 'format': yellow_fmt})
                        worksheet.conditional_format(f"{col_letter}2:{col_letter}100", {'type': 'cell', 'criteria': '<', 'value': 0.25, 'format': red_fmt})
                        
    def generate_radar_charts(self, output_dir: str):
        os.makedirs(output_dir, exist_ok=True)
        
        # Latest year
        idx = self.df.groupby('company_id')['year_dt'].idxmax()
        latest = self.df.loc[idx]
        
        metrics = ['return_on_equity_pct', 'return_on_capital_pct', 'net_profit_margin_pct', 'debt_to_equity',
                   'free_cash_flow_cr', 'pat_cagr_5yr', 'revenue_cagr_5yr', 'eps_cagr_5yr']
                   
        for _, row in latest.iterrows():
            c_id = row['company_id']
            group = row['peer_group_name']
            
            fig = plt.figure(figsize=(6, 6))
            ax = fig.add_subplot(111, polar=True)
            
            # Use percentiles if available
            p_df = self.percentiles_df[(self.percentiles_df['company_id'] == c_id) & (self.percentiles_df['year'] == row['year'])]
            
            angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
            angles += angles[:1]
            
            if not p_df.empty and pd.notna(group):
                values = []
                peer_avgs = []
                for m in metrics:
                    val = p_df[p_df['metric'] == m]['percentile_rank']
                    values.append(val.iloc[0] if not val.empty else 0.5)
                    peer_avgs.append(0.5) # Average percentile is 0.5
                values += values[:1]
                peer_avgs += peer_avgs[:1]
                
                ax.plot(angles, values, color='blue', linewidth=2, label=c_id)
                ax.fill(angles, values, color='blue', alpha=0.25)
                
                ax.plot(angles, peer_avgs, color='gray', linestyle='dashed', linewidth=2, label=f"{group} Avg")
            else:
                values = [0.5]*len(metrics) + [0.5]
                ax.plot(angles, values, color='red', linewidth=2, label='No peer group assigned')
                
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(metrics, size=8)
            plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
            plt.title(f"{c_id} Radar Chart")
            
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, f"{c_id}_radar.png"))
            plt.close(fig)

if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    db_path = os.path.join(base_dir, 'data', 'nifty100.db')
    
    engine = PeerEngine(db_path)
    engine.load_data()
    engine.compute_percentiles()
    
    engine.generate_excel(os.path.join(base_dir, 'output', 'peer_comparison.xlsx'))
    engine.generate_radar_charts(os.path.join(base_dir, 'reports', 'radar_charts'))
