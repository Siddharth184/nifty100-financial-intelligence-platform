"""
KMeans Clustering & Profiling Engine — Sprint 6 Days 36 & 37.

Implements:
- KMeans clustering with 5 clusters on 5 financial features
- Sector-median imputation for missing values
- StandardScaler normalization
- Elbow plot generation (k=2..10)
- Cluster profiling with descriptive names
- Correlation heatmap (Pearson, 10 KPIs)
- Sector-relative outlier detection (Z-score > 3)
- Portfolio statistics (P10..P90, Mean, Std)
"""

import os
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


try:
    import seaborn as sns
except ImportError:
    sns = None

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

from src.utils.logger import get_logger
from src.db.connection import get_db_connection

logger = get_logger(__name__)

DB_PATH = "db/nifty100.db"

CLUSTER_FEATURES = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",           # proxy for FCF CAGR (fcf_cagr_5yr not in DB)
    "operating_profit_margin_pct",
]

KPI_COLS_10 = [
    "return_on_equity_pct",
    "roce",
    "net_profit_margin_pct",
    "debt_to_equity",
    "free_cash_flow_cr",
    "cagr_pat_5yr",
    "cagr_sales_5yr",
    "cagr_eps_5yr",
    "interest_coverage",
    "asset_turnover",
]

# ── Fallback column mapping (handle both old/new column names) ─────────────
FEATURE_FALLBACKS = {
    "return_on_equity_pct": ["return_on_equity_pct", "roe"],
    "debt_to_equity": ["debt_to_equity"],
    "revenue_cagr_5yr": ["revenue_cagr_5yr", "cagr_sales_5yr"],
    "pat_cagr_5yr": ["pat_cagr_5yr", "cagr_pat_5yr"],
    "operating_profit_margin_pct": ["operating_profit_margin_pct", "opm"],
    "net_profit_margin_pct": ["net_profit_margin_pct", "npm"],
}


def _resolve_col(df: pd.DataFrame, canonical: str) -> str:
    """Resolves a canonical feature name to the actual column present in df."""
    for candidate in FEATURE_FALLBACKS.get(canonical, [canonical]):
        if candidate in df.columns:
            return candidate
    return canonical


def load_latest_features(db_path: str = DB_PATH) -> pd.DataFrame:
    """Loads latest-year financial features for all 92 companies with sector info."""
    with get_db_connection(db_path) as conn:
        df = pd.read_sql_query("""
            SELECT fr.*, c.company_name, c.ticker, s.sector_name
            FROM financial_ratios fr
            JOIN companies c ON fr.company_id = c.company_id
            LEFT JOIN sectors s ON c.sector_id = s.sector_id
            WHERE fr.year = (SELECT MAX(fr2.year) FROM financial_ratios fr2 WHERE fr2.company_id = fr.company_id)
            ORDER BY fr.company_id
        """, conn)
    return df


def impute_with_sector_median(df: pd.DataFrame, features: List[str]) -> pd.DataFrame:
    """Imputes missing feature values with sector median for each metric."""
    result = df.copy()
    for feat in features:
        col = _resolve_col(result, feat)
        if col not in result.columns:
            result[col] = np.nan
        # Sector-median imputation
        sector_medians = result.groupby("sector_name")[col].transform("median")
        mask = result[col].isna()
        result.loc[mask, col] = sector_medians[mask]
        # Global median fallback if any sectors have all NaN
        global_median = result[col].median()
        result[col] = result[col].fillna(global_median if pd.notna(global_median) else 0.0)
    return result


def run_kmeans_clustering(
    db_path: str = DB_PATH,
    n_clusters: int = 5,
    random_state: int = 42,
) -> pd.DataFrame:
    """
    Runs KMeans clustering on 92 companies.
    Returns DataFrame with company_id, cluster_id, cluster_name, distance_from_centroid.
    """
    logger.info("Day 36: Running KMeans Clustering (k=%d)...", n_clusters)
    df = load_latest_features(db_path)

    if df.empty:
        logger.error("No data loaded for clustering.")
        return pd.DataFrame()

    # Resolve actual column names
    resolved_features = [_resolve_col(df, f) for f in CLUSTER_FEATURES]

    # Impute missing values
    df = impute_with_sector_median(df, CLUSTER_FEATURES)

    # Extract feature matrix
    X = df[resolved_features].values.astype(float)

    # Standardize
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # KMeans
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    labels = kmeans.fit_predict(X_scaled)

    # Distance from centroid
    distances = []
    for i, label in enumerate(labels):
        dist = np.linalg.norm(X_scaled[i] - kmeans.cluster_centers_[label])
        distances.append(round(dist, 4))

    df["cluster_id"] = labels
    df["distance_from_centroid"] = distances

    # Profile clusters to assign names
    cluster_profiles = profile_clusters(df, resolved_features)
    name_map = assign_cluster_names(cluster_profiles)
    df["cluster_name"] = df["cluster_id"].map(name_map)

    # Export cluster_labels.csv
    os.makedirs("output", exist_ok=True)
    out_df = df[["company_id", "cluster_id", "cluster_name", "distance_from_centroid"]].copy()
    out_df.to_csv("output/cluster_labels.csv", index=False)
    logger.info("Exported output/cluster_labels.csv with %d companies.", len(out_df))

    # Generate elbow plot
    generate_elbow_plot(X_scaled, random_state)

    return out_df


def generate_elbow_plot(
    X_scaled: np.ndarray,
    random_state: int = 42,
    k_range: range = range(2, 11),
    output_path: str = "reports/elbow_plot.png",
):
    """Generates elbow plot (inertia vs k) and saves to reports/elbow_plot.png."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    inertias = []
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        km.fit(X_scaled)
        inertias.append(km.inertia_)

    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
    ax.plot(list(k_range), inertias, marker='o', linewidth=2, color='#1E3A8A')
    ax.axvline(x=5, linestyle='--', color='#EF4444', alpha=0.7, label='k=5 (selected)')
    ax.set_xlabel("Number of Clusters (k)", fontsize=11)
    ax.set_ylabel("Inertia (Within-Cluster Sum of Squares)", fontsize=11)
    ax.set_title("KMeans Elbow Plot — Nifty 100 Universe", fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(axis='y', linestyle='--', alpha=0.3)
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    logger.info("Saved elbow plot to %s", output_path)


def profile_clusters(df: pd.DataFrame, features: List[str]) -> pd.DataFrame:
    """Computes mean and median of clustering features per cluster."""
    agg_dict = {}
    for f in features:
        agg_dict[f] = ["mean", "median"]
    profiles = df.groupby("cluster_id").agg(agg_dict)
    profiles.columns = ["_".join(col) for col in profiles.columns]
    profiles["count"] = df.groupby("cluster_id").size()
    return profiles


def assign_cluster_names(profiles: pd.DataFrame) -> Dict[int, str]:
    """
    Assigns descriptive financial names to clusters based on centroid characteristics.
    Names are derived from the actual data, not hard-coded.
    """
    name_map = {}
    roe_col = [c for c in profiles.columns if "return_on_equity" in c and "mean" in c]
    de_col = [c for c in profiles.columns if "debt_to_equity" in c and "mean" in c]
    cagr_col = [c for c in profiles.columns if "cagr" in c and "mean" in c]
    opm_col = [c for c in profiles.columns if "operating_profit" in c or "opm" in c]
    opm_col = [c for c in opm_col if "mean" in c]

    roe_mean = roe_col[0] if roe_col else None
    de_mean = de_col[0] if de_col else None

    # Score each cluster by composite rank
    cluster_scores = {}
    for cid in profiles.index:
        roe_v = profiles.loc[cid, roe_mean] if roe_mean else 0
        de_v = profiles.loc[cid, de_mean] if de_mean else 0
        cagr_v = profiles.loc[cid, cagr_col[0]] if cagr_col else 0
        opm_v = profiles.loc[cid, opm_col[0]] if opm_col else 0
        # Composite: higher ROE, lower D/E, higher CAGR, higher OPM = better
        score = (roe_v or 0) - (de_v or 0) * 5 + (cagr_v or 0) + (opm_v or 0)
        cluster_scores[cid] = score

    sorted_clusters = sorted(cluster_scores.keys(), key=lambda x: cluster_scores[x], reverse=True)

    candidate_names = [
        "High-Quality Compounders",
        "Defensive Stalwarts",
        "Emerging Growth",
        "Value Cyclicals",
        "Leveraged Turnaround",
    ]

    for rank, cid in enumerate(sorted_clusters):
        name_map[cid] = candidate_names[rank] if rank < len(candidate_names) else f"Cluster {cid}"

    return name_map


# ── Day 37 Functions ──────────────────────────────────────────────────────────

def generate_correlation_heatmap(
    db_path: str = DB_PATH,
    output_path: str = "reports/correlation_heatmap.png",
):
    """Generates Pearson correlation heatmap of 10 KPIs for latest year."""
    logger.info("Day 37: Generating Correlation Heatmap...")
    df = load_latest_features(db_path)
    if df.empty:
        logger.warning("No data for correlation heatmap.")
        return

    resolved = []
    labels = []
    kpi_labels = {
        "return_on_equity_pct": "ROE %", "roe": "ROE %",
        "roce": "ROCE %",
        "net_profit_margin_pct": "NPM %", "npm": "NPM %",
        "debt_to_equity": "D/E",
        "free_cash_flow_cr": "FCF (Cr)", "free_cash_flow": "FCF (Cr)",
        "cagr_pat_5yr": "PAT CAGR 5Y",
        "cagr_sales_5yr": "Rev CAGR 5Y",
        "cagr_eps_5yr": "EPS CAGR 5Y",
        "interest_coverage": "ICR",
        "asset_turnover": "Asset T/O",
    }
    for col in KPI_COLS_10:
        actual = _resolve_col(df, col)
        if actual in df.columns:
            resolved.append(actual)
            labels.append(kpi_labels.get(actual, actual))

    if not resolved:
        logger.warning("No KPI columns found for heatmap.")
        return

    corr = df[resolved].corr(method="pearson")
    corr.index = labels
    corr.columns = labels

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 8), dpi=150)
    if sns is not None:
        sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu_r", center=0,
                    square=True, linewidths=0.5, ax=ax,
                    cbar_kws={"shrink": 0.8})
    else:
        im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1)
        ax.set_xticks(range(len(labels)))
        ax.set_yticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha='right')
        ax.set_yticklabels(labels)
        plt.colorbar(im, ax=ax, shrink=0.8)

    ax.set_title("Pearson Correlation — 10 KPIs (Latest Year, 92 Companies)",
                 fontsize=13, fontweight='bold', pad=12)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    logger.info("Saved correlation heatmap to %s", output_path)


def generate_outlier_report(
    db_path: str = DB_PATH,
    output_path: str = "output/outlier_report.csv",
):
    """Generates sector-relative Z-score outlier report. Flags |Z| > 3."""
    logger.info("Day 37: Generating Outlier Report...")
    df = load_latest_features(db_path)
    if df.empty:
        return pd.DataFrame()

    resolved_kpis = [_resolve_col(df, c) for c in KPI_COLS_10]
    resolved_kpis = [c for c in resolved_kpis if c in df.columns]

    outlier_rows = []
    for sector, grp in df.groupby("sector_name"):
        for col in resolved_kpis:
            vals = grp[col].dropna()
            if len(vals) < 3:
                continue
            mean_v = vals.mean()
            std_v = vals.std()
            if std_v == 0:
                continue
            z_scores = (grp[col] - mean_v) / std_v
            flagged = grp[z_scores.abs() > 3]
            for _, row in flagged.iterrows():
                outlier_rows.append({
                    "company_id": row["company_id"],
                    "company_name": row.get("company_name", ""),
                    "sector": sector,
                    "metric": col,
                    "value": round(float(row[col]), 4) if pd.notna(row[col]) else None,
                    "z_score": round(float(z_scores.loc[row.name]), 4),
                })

    out_df = pd.DataFrame(outlier_rows)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    out_df.to_csv(output_path, index=False)
    logger.info("Saved outlier report to %s (%d outliers found).", output_path, len(out_df))
    return out_df


def generate_portfolio_stats(
    db_path: str = DB_PATH,
    output_path: str = "output/portfolio_stats.csv",
):
    """Generates P10, P25, P50, P75, P90, Mean, Std for each KPI."""
    logger.info("Day 37: Generating Portfolio Stats...")
    df = load_latest_features(db_path)
    if df.empty:
        return pd.DataFrame()

    resolved_kpis = [_resolve_col(df, c) for c in KPI_COLS_10]
    resolved_kpis = [c for c in resolved_kpis if c in df.columns]

    stats_rows = []
    for col in resolved_kpis:
        vals = df[col].dropna()
        if vals.empty:
            continue
        stats_rows.append({
            "metric": col,
            "P10": round(float(np.percentile(vals, 10)), 4),
            "P25": round(float(np.percentile(vals, 25)), 4),
            "P50": round(float(np.percentile(vals, 50)), 4),
            "P75": round(float(np.percentile(vals, 75)), 4),
            "P90": round(float(np.percentile(vals, 90)), 4),
            "Mean": round(float(vals.mean()), 4),
            "Std": round(float(vals.std()), 4),
        })

    out_df = pd.DataFrame(stats_rows)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    out_df.to_csv(output_path, index=False)
    logger.info("Saved portfolio stats to %s (%d metrics).", output_path, len(out_df))
    return out_df


# ── Main Entrypoint ───────────────────────────────────────────────────────────

def run_all_day36_37(db_path: str = DB_PATH):
    """Runs all Day 36 and Day 37 deliverables."""
    # Day 36
    cluster_df = run_kmeans_clustering(db_path)
    print(f"Cluster Labels: {len(cluster_df)} companies assigned")
    print(f"Cluster Distribution:\n{cluster_df['cluster_name'].value_counts()}")

    # Day 37
    generate_correlation_heatmap(db_path)
    outlier_df = generate_outlier_report(db_path)
    print(f"Outliers flagged: {len(outlier_df)}")
    stats_df = generate_portfolio_stats(db_path)
    print(f"Portfolio stats generated for {len(stats_df)} metrics")


if __name__ == "__main__":
    run_all_day36_37()
