"""Parse CK output CSVs and compute per-repository quality metric summaries."""

import csv
import statistics
from pathlib import Path
from typing import Dict, List

from config import Config


# CK class.csv columns we care about for RQs 1-4.
# - cbo, dit, lcom: quality metrics (distributions summarised per repo)
# - loc: also summarised per class, but additionally summed to give a repo-level
#   Size metric for RQ04.
_METRIC_COLUMNS = ("cbo", "dit", "lcom", "loc")


def _read_class_rows(class_csv: Path) -> List[Dict[str, str]]:
    """Return all rows from CK's class.csv as a list of dicts."""
    with open(class_csv, "r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        return list(reader)


def _coerce_float(raw: str) -> float:
    """Convert a CSV cell to float, returning NaN for empty/invalid values."""
    try:
        return float(raw)
    except (TypeError, ValueError):
        return float("nan")


def _collect_metric_values(rows: List[Dict[str, str]], column: str) -> List[float]:
    """Extract numeric values for *column* from *rows*, skipping NaNs."""
    values: List[float] = []
    for row in rows:
        raw = row.get(column, "")
        value = _coerce_float(raw)
        if value == value:  # filter NaN
            values.append(value)
    return values


def _summarise(values: List[float]) -> Dict[str, float]:
    """Return mean, median, and population stdev for *values*."""
    if not values:
        return {"mean": 0.0, "median": 0.0, "stdev": 0.0}

    mean = statistics.fmean(values)
    median = statistics.median(values)
    stdev = statistics.pstdev(values) if len(values) > 1 else 0.0

    return {
        "mean": round(mean, 4),
        "median": round(median, 4),
        "stdev": round(stdev, 4),
    }


def summarise_ck_output(ck_output_dir: Path) -> Dict[str, float]:
    """
    Read CK's class.csv in *ck_output_dir* and compute summary statistics.

    Returns a flat dict containing:

    - ``ck_class_count``: number of Java classes analysed by CK
    - ``loc_total``: total lines of code (sum of per-class ``loc``) -- the
      repository Size metric used for RQ04
    - ``{cbo,dit,lcom,loc}_{mean,median,stdev}``: distribution stats per class

    If ``class.csv`` is missing or empty, all numeric fields default to 0.
    """
    class_csv = ck_output_dir / Config.CK_CLASS_FILE

    summary: Dict[str, float] = {"ck_class_count": 0, "loc_total": 0}
    for metric in _METRIC_COLUMNS:
        summary[f"{metric}_mean"] = 0.0
        summary[f"{metric}_median"] = 0.0
        summary[f"{metric}_stdev"] = 0.0

    if not class_csv.is_file():
        return summary

    rows = _read_class_rows(class_csv)
    summary["ck_class_count"] = len(rows)

    for metric in _METRIC_COLUMNS:
        values = _collect_metric_values(rows, metric)
        stats = _summarise(values)
        summary[f"{metric}_mean"] = stats["mean"]
        summary[f"{metric}_median"] = stats["median"]
        summary[f"{metric}_stdev"] = stats["stdev"]

        if metric == "loc":
            summary["loc_total"] = int(sum(values))

    return summary
