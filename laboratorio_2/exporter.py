"""CSV export utilities for repository lists and metric summaries."""

import csv
from pathlib import Path
from typing import Dict, List


REPO_LIST_FIELDS = [
    "owner",
    "name",
    "full_name",
    "url",
    "stars",
    "releases",
    "age_years",
    "created_at",
]

METRICS_FIELDS = [
    "owner",
    "name",
    "full_name",
    "stars",
    "releases",
    "age_years",
    "ck_class_count",
    "loc_total",
    "cbo_mean",
    "cbo_median",
    "cbo_stdev",
    "dit_mean",
    "dit_median",
    "dit_stdev",
    "lcom_mean",
    "lcom_median",
    "lcom_stdev",
    "loc_mean",
    "loc_median",
    "loc_stdev",
]


def _ensure_output_dir(output_dir: Path) -> None:
    """Create *output_dir* and any missing parent directories."""
    output_dir.mkdir(parents=True, exist_ok=True)


def _write_csv(filepath: Path, fieldnames: List[str], rows: List[Dict]) -> None:
    """Write *rows* to a CSV file at *filepath* using *fieldnames* as header."""
    with open(filepath, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def save_repo_list(repositories: List[Dict], filepath: Path) -> Path:
    """
    Write the list of collected repositories to a CSV file.

    Only the columns defined in REPO_LIST_FIELDS are written.
    Returns the path of the written file.
    """
    _ensure_output_dir(filepath.parent)
    _write_csv(filepath, REPO_LIST_FIELDS, repositories)
    return filepath


def save_metrics(records: List[Dict], filepath: Path) -> Path:
    """
    Write the combined process + quality metrics per repository to a CSV file.

    Only the columns defined in METRICS_FIELDS are written.
    Returns the path of the written file.
    """
    _ensure_output_dir(filepath.parent)
    _write_csv(filepath, METRICS_FIELDS, records)
    return filepath
