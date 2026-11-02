"""
Clustering and Portfolio Statistics Module for Nifty 100 Financial Intelligence Platform.
Implements KMeans clustering (5 clusters), elbow curve analysis, cluster profiling,
Pearson correlation heatmap, sector-relative Z-score outlier detection, and portfolio distribution statistics.
"""

import os
import sqlite3
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans


def load_clustering_features(db_path=None, base_dir=None):
    """
    Load latest year financial ratios and compute/merge clustering features for all 92 companies:
    - return_on_equity_pct
    - debt_to_equity
    - revenue_cagr_5yr
    - fcf_cagr_5yr
    - operating_profit_margin_pct
    """
    if base_dir is None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if db_path is None:
        db_path = os.path.join(base_dir, 'data', 'nifty100.db')

    conn = sqlite3.connect(db_path)
    companies = pd.read_sql('SELECT id, company_name FROM companies ORDER BY id', conn)
    sectors = pd.read_sql('SELECT company_id, broad_sector, sub_sector FROM sectors', conn)
    ratios = pd.read_sql('SELECT * FROM financial_ratios', conn)
    conn.close()

    ratios['year_dt'] = pd.to_datetime(ratios['year'].astype(str))

    # Pull FCF CAGR 5yr from cashflow_intelligence if available, or compute from free_cash_flow_cr
    cf_intel_path = os.path.join(base_dir, 'output', 'cashflow_intelligence.xlsx')
    fcf_cagr_map = {}
    if os.path.exists(cf_intel_path):
        cf_df = pd.read_excel(cf_intel_path)
        fcf_cagr_map = cf_df.set_index('company_id')['fcf_cagr_5yr'].to_dict()

    feature_rows = []
    for cid in companies['id']:
        c_r = ratios[ratios['company_id'] == cid].sort_values('year_dt')
        c_sec = sectors[sectors['company_id'] == cid]
        sec_name = c_sec.iloc[0]['broad_sector'] if not c_sec.empty else 'Unknown'

        if not c_r.empty:
            lat = c_r.iloc[-1]
            roe = lat.get('return_on_equity_pct')
            de = lat.get('debt_to_equity')
            rev_cagr = lat.get('revenue_cagr_5yr')
            opm = lat.get('operating_profit_margin_pct')
            
            # FCF CAGR
            fcf_cagr = fcf_cagr_map.get(cid)
            if pd.isna(fcf_cagr) or fcf_cagr is None:
                # Fallback compute from ratios if 5 years available
                c_fcf = c_r.dropna(subset=['free_cash_flow_cr'])
                if len(c_fcf) >= 5:
                    start_f = c_fcf.iloc[-5]['free_cash_flow_cr']
                    end_f = c_fcf.iloc[-1]['free_cash_flow_cr']
                    if start_f > 0 and end_f > 0:
                        fcf_cagr = ((end_f / start_f) ** (1.0 / 5.0) - 1.0) * 100.0
                    else:
                        fcf_cagr = np.nan
                else:
                    fcf_cagr = np.nan
        else:
            roe, de, rev_cagr, opm, fcf_cagr = np.nan, np.nan, np.nan, np.nan, np.nan

        feature_rows.append({
            'company_id': cid,
            'broad_sector': sec_name,
            'return_on_equity_pct': roe,
            'debt_to_equity': de,
            'revenue_cagr_5yr': rev_cagr,
            'fcf_cagr_5yr': fcf_cagr,
            'operating_profit_margin_pct': opm
        })

    df = pd.DataFrame(feature_rows)
    return df


def impute_features(df, feature_cols):
    """
    Impute missing values using sector median for each metric.
    Fallback to overall metric median if sector median is NaN.
    """
    df_imputed = df.copy()
    for col in feature_cols:
        overall_med = df_imputed[col].median()
        if pd.isna(overall_med):
            overall_med = 0.0

        # Group by broad_sector and transform median
        sector_meds = df_imputed.groupby('broad_sector')[col].transform('median')
        df_imputed[col] = df_imputed[col].fillna(sector_meds).fillna(overall_med)

    return df_imputed


def run_kmeans_clustering(base_dir=None):
    """
    Perform KMeans clustering with k=5 on normalized financial features.
    Generates:
    - reports/elbow_plot.png
    - reports/correlation_heatmap.png
    - output/cluster_labels.csv
    - output/outlier_report.csv
    - output/portfolio_stats.csv
    """
    if base_dir is None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

    output_dir = os.path.join(base_dir, 'output')
    reports_dir = os.path.join(base_dir, 'reports')
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    df_raw = load_clustering_features(base_dir=base_dir)
    feature_cols = [
        'return_on_equity_pct',
        'debt_to_equity',
        'revenue_cagr_5yr',
        'fcf_cagr_5yr',
        'operating_profit_margin_pct'
    ]

    df_imputed = impute_features(df_raw, feature_cols)

    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df_imputed[feature_cols])

    # 1. Elbow Plot (k from 2 to 10)
    k_range = list(range(2, 11))
    inertias = []
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(X_scaled)
        inertias.append(km.inertia_)

    plt.close('all')
    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=200)
    ax.plot(k_range, inertias, marker='o', linewidth=2, color='#2B6CB0', markersize=6)
    ax.axvline(x=5, color='#E53E3E', linestyle='--', linewidth=1.5, label='Optimal k = 5')
    ax.scatter([5], [inertias[3]], color='#E53E3E', s=100, zorder=5)
    ax.set_title('KMeans Clustering Elbow Curve: Inertia vs Number of Clusters (k)', fontsize=11, fontweight='bold', pad=10, color='#1A365D')
    ax.set_xlabel('Number of Clusters (k)', fontsize=9.5)
    ax.set_ylabel('Inertia (Within-Cluster Sum of Squares)', fontsize=9.5)
    ax.set_xticks(k_range)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(frameon=True, facecolor='#FFFFFF', edgecolor='#CBD5E0')
    plt.tight_layout()
    elbow_path = os.path.join(reports_dir, 'elbow_plot.png')
    plt.savefig(elbow_path)
    plt.close(fig)
    print(f"Saved elbow curve to {elbow_path}")

    # 2. Fit Final KMeans with k=5
    kmeans_5 = KMeans(n_clusters=5, random_state=42, n_init=15)
    cluster_labels = kmeans_5.fit_predict(X_scaled)
    centroids = kmeans_5.cluster_centers_

    # Calculate distance from centroid for each company
    distances = np.linalg.norm(X_scaled - centroids[cluster_labels], axis=1)

    df_imputed['cluster_id'] = cluster_labels
    df_imputed['distance_from_centroid'] = np.round(distances, 4)

    # 3. Profile Clusters to assign descriptive archetype names
    cluster_profiles = {}
    for cid in range(5):
        c_sub = df_imputed[df_imputed['cluster_id'] == cid]
        means = c_sub[feature_cols].mean().to_dict()
        meds = c_sub[feature_cols].median().to_dict()
        cluster_profiles[cid] = {'count': len(c_sub), 'means': means, 'medians': meds}

    # Archetype assignment based on financial characteristics:
    # Cluster characteristics scoring
    # We rank clusters by median ROE, D/E, Rev CAGR, OPM
    assigned_names = {}
    used_names = set()

    # Identify distinct archetype definitions:
    # 1. Distressed or Turnaround: Highest D/E or Negative/Low ROE or Low FCF CAGR
    # 2. High-Quality Compounders: Highest ROE and OPM, low D/E
    # 3. Emerging Growth: High Revenue CAGR
    # 4. Defensive Dividend Payers: Low D/E, moderate steady ROE, moderate OPM
    # 5. Value Cyclicals: Moderate/High capital intensity, cyclical OPM
    sorted_by_roe = sorted(range(5), key=lambda c: cluster_profiles[c]['medians']['return_on_equity_pct'], reverse=True)
    sorted_by_de = sorted(range(5), key=lambda c: cluster_profiles[c]['medians']['debt_to_equity'], reverse=True)
    sorted_by_growth = sorted(range(5), key=lambda c: cluster_profiles[c]['medians']['revenue_cagr_5yr'], reverse=True)

    # Highest D/E or lowest ROE -> Distressed or Turnaround
    distressed_cand = sorted_by_de[0]
    assigned_names[distressed_cand] = "Distressed or Turnaround"
    used_names.add("Distressed or Turnaround")

    # Highest ROE among remaining -> High-Quality Compounders
    for c in sorted_by_roe:
        if c not in assigned_names:
            assigned_names[c] = "High-Quality Compounders"
            used_names.add("High-Quality Compounders")
            break

    # Highest growth among remaining -> Emerging Growth
    for c in sorted_by_growth:
        if c not in assigned_names:
            assigned_names[c] = "Emerging Growth"
            used_names.add("Emerging Growth")
            break

    # Remaining two: Value Cyclicals and Defensive Dividend Payers
    remaining = [c for c in range(5) if c not in assigned_names]
    if len(remaining) == 2:
        c1, c2 = remaining[0], remaining[1]
        # Compare D/E or OPM
        if cluster_profiles[c1]['medians']['debt_to_equity'] > cluster_profiles[c2]['medians']['debt_to_equity']:
            assigned_names[c1] = "Value Cyclicals"
            assigned_names[c2] = "Defensive Dividend Payers"
        else:
            assigned_names[c1] = "Defensive Dividend Payers"
            assigned_names[c2] = "Value Cyclicals"
    else:
        fallback_names = ["Defensive Dividend Payers", "Value Cyclicals", "Emerging Growth"]
        for c in range(5):
            if c not in assigned_names:
                for fn in fallback_names:
                    if fn not in used_names:
                        assigned_names[c] = fn
                        used_names.add(fn)
                        break

    df_imputed['cluster_name'] = df_imputed['cluster_id'].map(assigned_names)

    # Save output/cluster_labels.csv
    labels_csv = os.path.join(output_dir, 'cluster_labels.csv')
    df_imputed[['company_id', 'cluster_id', 'cluster_name', 'distance_from_centroid']].to_csv(labels_csv, index=False)
    print(f"Saved cluster labels for all 92 companies to {labels_csv}")
    for cid in range(5):
        print(f"  Cluster {cid} ({assigned_names[cid]}): {len(df_imputed[df_imputed['cluster_id'] == cid])} companies")

    # 4. Pearson Correlation Heatmap across 10 KPIs
    conn = sqlite3.connect(os.path.join(base_dir, 'data', 'nifty100.db'))
    ratios_all = pd.read_sql('SELECT * FROM financial_ratios', conn)
    mc_all = pd.read_sql('SELECT company_id, year, pe_ratio, pb_ratio, dividend_yield_pct FROM market_cap', conn)
    conn.close()

    ratios_all['year_dt'] = pd.to_datetime(ratios_all['year'].astype(str))
    mc_all['year_dt'] = pd.to_datetime(mc_all['year'].astype(str))

    lat_r_idx = ratios_all.groupby('company_id')['year_dt'].idxmax()
    lat_r = ratios_all.loc[lat_r_idx]

    lat_mc_idx = mc_all.groupby('company_id')['year_dt'].idxmax()
    lat_mc = mc_all.loc[lat_mc_idx]

    merged_kpi = lat_r.merge(lat_mc[['company_id', 'pe_ratio', 'pb_ratio', 'dividend_yield_pct']], on='company_id', how='left')

    kpi_cols = [
        'return_on_equity_pct',
        'return_on_capital_pct',
        'operating_profit_margin_pct',
        'net_profit_margin_pct',
        'debt_to_equity',
        'interest_coverage',
        'revenue_cagr_5yr',
        'pat_cagr_5yr',
        'pe_ratio',
        'pb_ratio'
    ]
    kpi_names = [
        'ROE (%)', 'ROCE (%)', 'OPM (%)', 'NPM (%)', 'D/E (x)',
        'ICR (x)', 'Rev CAGR 5Y', 'PAT CAGR 5Y', 'P/E (x)', 'P/B (x)'
    ]

    corr_df = merged_kpi[kpi_cols].astype(float).corr(method='pearson')
    corr_df.columns = kpi_names
    corr_df.index = kpi_names

    plt.close('all')
    fig, ax = plt.subplots(figsize=(8.5, 7), dpi=200)
    sns.heatmap(
        corr_df,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        vmin=-1,
        vmax=1,
        linewidths=0.5,
        cbar_kws={'label': 'Pearson Correlation Coefficient'},
        ax=ax,
        annot_kws={"size": 7.5}
    )
    ax.set_title('10-KPI Pearson Correlation Matrix Heatmap (Latest Year)', fontsize=11, fontweight='bold', pad=12, color='#1A365D')
    plt.xticks(rotation=45, ha='right', fontsize=8)
    plt.yticks(rotation=0, fontsize=8)
    plt.tight_layout()
    heatmap_path = os.path.join(reports_dir, 'correlation_heatmap.png')
    plt.savefig(heatmap_path)
    plt.close(fig)
    print(f"Saved correlation heatmap to {heatmap_path}")

    # 5. Sector-relative Outlier Detection (|Z-score| > 3)
    outliers = []
    sectors_df = pd.read_sql('SELECT company_id, broad_sector FROM sectors', sqlite3.connect(os.path.join(base_dir, 'data', 'nifty100.db')))
    kpi_full = merged_kpi.merge(sectors_df, on='company_id', how='left')

    for col in kpi_cols:
        for sec, group in kpi_full.groupby('broad_sector'):
            vals = group[col].dropna()
            if len(vals) >= 3:
                mean = vals.mean()
                std = vals.std()
                if std > 0:
                    for _, row in group.iterrows():
                        v = row[col]
                        if pd.notna(v):
                            z = (v - mean) / std
                            if abs(z) > 3.0:
                                outliers.append({
                                    'company_id': row['company_id'],
                                    'broad_sector': sec,
                                    'metric': col,
                                    'metric_value': round(v, 2),
                                    'sector_mean': round(mean, 2),
                                    'sector_std': round(std, 2),
                                    'z_score': round(z, 2),
                                    'outlier_type': 'Extreme Positive' if z > 3.0 else 'Extreme Negative'
                                })

    outlier_df = pd.DataFrame(outliers)
    outlier_csv = os.path.join(output_dir, 'outlier_report.csv')
    outlier_df.to_csv(outlier_csv, index=False)
    print(f"Saved {len(outlier_df)} sector outlier alerts to {outlier_csv}")

    # 6. Portfolio Statistics (P10, P25, P50, P75, P90, Mean, Std)
    stats_list = []
    for col, display_name in zip(kpi_cols, kpi_names):
        vals = merged_kpi[col].dropna()
        if len(vals) > 0:
            stats_list.append({
                'metric': display_name,
                'raw_metric': col,
                'count': len(vals),
                'mean': round(vals.mean(), 2),
                'std': round(vals.std(), 2),
                'p10': round(vals.quantile(0.10), 2),
                'p25': round(vals.quantile(0.25), 2),
                'p50_median': round(vals.quantile(0.50), 2),
                'p75': round(vals.quantile(0.75), 2),
                'p90': round(vals.quantile(0.90), 2)
            })

    stats_df = pd.DataFrame(stats_list)
    stats_csv = os.path.join(output_dir, 'portfolio_stats.csv')
    stats_df.to_csv(stats_csv, index=False)
    print(f"Saved portfolio distribution statistics to {stats_csv}")

    return df_imputed, stats_df, outlier_df


if __name__ == '__main__':
    run_kmeans_clustering()
