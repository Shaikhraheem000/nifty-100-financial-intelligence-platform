"""
Unit and integration tests for ML Clustering, Outlier Detection, and Portfolio Statistics.
"""

import os
import pandas as pd
import pytest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def test_cluster_labels_complete_92_companies():
    cluster_csv = os.path.join(BASE_DIR, 'output', 'cluster_labels.csv')
    assert os.path.exists(cluster_csv), "cluster_labels.csv does not exist"

    df = pd.read_csv(cluster_csv)
    assert len(df) == 92, f"Expected 92 companies in cluster_labels.csv, got {len(df)}"
    assert {'company_id', 'cluster_id', 'cluster_name', 'distance_from_centroid'}.issubset(df.columns)

    # Check 5 clusters (0 to 4) are present
    unique_clusters = set(df['cluster_id'].unique())
    assert unique_clusters == {0, 1, 2, 3, 4}

    # All distances are positive floats
    assert (df['distance_from_centroid'] >= 0).all()


def test_portfolio_stats_has_10_kpis():
    stats_csv = os.path.join(BASE_DIR, 'output', 'portfolio_stats.csv')
    assert os.path.exists(stats_csv), "portfolio_stats.csv does not exist"

    df = pd.read_csv(stats_csv)
    assert len(df) == 10, f"Expected 10 KPIs in portfolio_stats.csv, got {len(df)}"
    expected_cols = {'metric', 'raw_metric', 'count', 'mean', 'std', 'p10', 'p25', 'p50_median', 'p75', 'p90'}
    assert expected_cols.issubset(df.columns)


def test_outlier_report_structure():
    outlier_csv = os.path.join(BASE_DIR, 'output', 'outlier_report.csv')
    assert os.path.exists(outlier_csv), "outlier_report.csv does not exist"

    df = pd.read_csv(outlier_csv)
    assert {'company_id', 'broad_sector', 'metric', 'z_score', 'outlier_type'}.issubset(df.columns)
    # Check that all flagged outliers have |z_score| > 3.0
    assert (df['z_score'].abs() > 3.0).all()


def test_visual_artifacts_generated():
    elbow_png = os.path.join(BASE_DIR, 'reports', 'elbow_plot.png')
    heatmap_png = os.path.join(BASE_DIR, 'reports', 'correlation_heatmap.png')

    assert os.path.exists(elbow_png), "elbow_plot.png does not exist"
    assert os.path.getsize(elbow_png) > 10000  # > 10 KB

    assert os.path.exists(heatmap_png), "correlation_heatmap.png does not exist"
    assert os.path.getsize(heatmap_png) > 10000  # > 10 KB
