"""
Analyse metrics_summary.csv for Lab 02 and produce the artifacts needed by
the final report:

  - output/analysis/descriptive_stats.csv   central-tendency table
  - output/analysis/spearman_correlations.csv
  - output/analysis/RQ01_popularity.png
  - output/analysis/RQ02_maturity.png
  - output/analysis/RQ03_activity.png
  - output/analysis/RQ04_size.png

The four plots cover the 12 correlation pairs (4 RQs × 3 quality metrics).

Usage:
    python analysis.py
    python analysis.py --metrics output/metrics_summary.csv \
                       --outdir output/analysis
"""

import argparse
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib

matplotlib.use("Agg")  # non-interactive backend (no display needed)

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402

from config import Config


# Mapping of RQ → (process metric column, human-readable label, use log X axis)
#
# Log axis on X makes sense for stars / loc_total / releases because their
# distributions are heavily right-skewed (power-law). Age in years is roughly
# uniform on [0, 15] so we keep it linear.
PROCESS_METRICS: Dict[str, Tuple[str, str, bool]] = {
    "RQ01_popularity": ("stars",     "Popularity (stars)",  True),
    "RQ02_maturity":   ("age_years", "Maturity (years)",    False),
    "RQ03_activity":   ("releases",  "Activity (releases)", True),
    "RQ04_size":       ("loc_total", "Size (total LOC)",    True),
}

# Quality metrics to correlate against each process metric.
# We use the median summary (not mean) because LCOM distributions are heavily
# skewed by test classes with many methods; the median represents the typical
# class much better.
QUALITY_METRICS: List[Tuple[str, str]] = [
    ("cbo_median",  "CBO (median)"),
    ("dit_median",  "DIT (median)"),
    ("lcom_median", "LCOM (median)"),
]


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Analyse Lab 02 metrics CSV and generate report artifacts."
    )
    default_metrics = str(Path(Config.OUTPUT_DIR) / Config.METRICS_CSV)
    default_outdir = str(Path(Config.OUTPUT_DIR) / "analysis")
    parser.add_argument(
        "--metrics", default=default_metrics,
        help="Path to metrics_summary.csv (default: %(default)s)."
    )
    parser.add_argument(
        "--outdir", default=default_outdir,
        help="Directory for analysis outputs (default: %(default)s)."
    )
    return parser


def load_dataframe(metrics_path: Path) -> pd.DataFrame:
    """
    Load metrics_summary.csv and drop repositories with no usable data.

    A repo is "unusable" if CK found zero classes (typically because the
    repo is misconfigured, non-Java, or the clone failed). We also filter
    out rows with loc_total == 0 for the same reason.
    """
    if not metrics_path.is_file():
        raise FileNotFoundError(
            f"{metrics_path} not found. Run main.py first to collect metrics."
        )

    df = pd.read_csv(metrics_path)
    before = len(df)
    df = df[(df["ck_class_count"] > 0) & (df["loc_total"] > 0)].copy()
    dropped = before - len(df)
    if dropped:
        print(f"Dropped {dropped} repositories with no CK data.")
    print(f"Analysing {len(df)} repositories.")
    return df


def descriptive_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Central-tendency table over all repositories.

    Columns shown: mean, median, std, min, max for both process and
    quality metrics. The PDF explicitly requires mediana/média/desvio padrão
    per repository, so we include all three.
    """
    cols = [
        "stars", "releases", "age_years", "loc_total", "ck_class_count",
        "cbo_mean", "cbo_median", "cbo_stdev",
        "dit_mean", "dit_median", "dit_stdev",
        "lcom_mean", "lcom_median", "lcom_stdev",
    ]
    cols = [c for c in cols if c in df.columns]
    summary = df[cols].agg(["mean", "median", "std", "min", "max"]).round(3)
    return summary.T  # one row per metric, easier to read


def spearman_correlations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Spearman's rho + p-value for all 12 (process × quality) pairs.

    Spearman is used instead of Pearson because:
      * Distributions of stars, releases, LOC are heavy-tailed (power-law).
      * Spearman only assumes monotonicity, not linearity.
      * It's robust to outliers, which matters a lot for the kind of data
        the GitHub top-1000 produces.
    """
    rows = []
    for rq_id, (x_col, x_label, _log_x) in PROCESS_METRICS.items():
        if x_col not in df.columns:
            continue
        for y_col, y_label in QUALITY_METRICS:
            if y_col not in df.columns:
                continue
            x = df[x_col].to_numpy()
            y = df[y_col].to_numpy()
            rho, pvalue = stats.spearmanr(x, y, nan_policy="omit")
            rows.append({
                "rq": rq_id,
                "x": x_col,
                "y": y_col,
                "n": int(np.isfinite(x).sum() & np.isfinite(y).sum()),
                "spearman_rho": round(float(rho), 4),
                "p_value": round(float(pvalue), 6),
                "significant_5pct": bool(pvalue < 0.05),
            })
    return pd.DataFrame(rows)


def plot_rq(
    df: pd.DataFrame,
    rq_id: str,
    x_col: str,
    x_label: str,
    log_x: bool,
    outdir: Path,
) -> Path:
    """Render a 1×3 scatter panel for one RQ and save as PNG."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))

    for ax, (y_col, y_label) in zip(axes, QUALITY_METRICS):
        x = df[x_col]
        y = df[y_col]

        ax.scatter(x, y, alpha=0.35, s=14, edgecolors="none")

        if log_x:
            # symlog handles zeros gracefully (repos with 0 releases)
            ax.set_xscale("symlog")

        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)

        rho, pvalue = stats.spearmanr(x, y, nan_policy="omit")
        sig = "*" if pvalue < 0.05 else ""
        ax.set_title(
            f"{y_label}\n"
            rf"Spearman $\rho$={rho:.3f}{sig} (p={pvalue:.2g}, n={len(df)})"
        )
        ax.grid(True, linestyle=":", alpha=0.4)

    fig.suptitle(f"{rq_id}: {x_label} vs. Quality Metrics", fontsize=14)
    fig.tight_layout()

    out_path = outdir / f"{rq_id}.png"
    fig.savefig(out_path, dpi=110, bbox_inches="tight")
    plt.close(fig)
    return out_path


def main() -> None:
    args = _build_arg_parser().parse_args()
    metrics_path = Path(args.metrics)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    df = load_dataframe(metrics_path)

    # --- 1. Descriptive statistics ---
    desc = descriptive_stats(df)
    desc_path = outdir / "descriptive_stats.csv"
    desc.to_csv(desc_path)
    print(f"\n[Descriptive stats] saved to {desc_path}")
    print(desc.to_string())

    # --- 2. Spearman correlations ---
    corr = spearman_correlations(df)
    corr_path = outdir / "spearman_correlations.csv"
    corr.to_csv(corr_path, index=False)
    print(f"\n[Spearman correlations] saved to {corr_path}")
    print(corr.to_string(index=False))

    # --- 3. Scatter plots (one per RQ) ---
    print("\n[Plots]")
    for rq_id, (x_col, x_label, log_x) in PROCESS_METRICS.items():
        if x_col not in df.columns:
            print(f"  skipped {rq_id}: column {x_col} missing")
            continue
        path = plot_rq(df, rq_id, x_col, x_label, log_x, outdir)
        print(f"  saved {path}")

    print("\nDone.")


if __name__ == "__main__":
    main()
