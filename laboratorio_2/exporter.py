"""CSV export utilities for repository lists and metric summaries."""

import csv
import threading
from pathlib import Path
from typing import Dict, List, Set


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


def load_processed_repos(filepath: Path) -> Set[str]:
    """
    Return the set of ``full_name`` values already present in *filepath*.

    Used by the pipeline's resume mode to skip repositories whose metrics
    have already been computed in a previous (possibly interrupted) run.
    Returns an empty set if the file does not exist or has no data rows.
    """
    if not filepath.exists() or filepath.stat().st_size == 0:
        return set()
    with open(filepath, "r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        return {row["full_name"] for row in reader if row.get("full_name")}


class IncrementalMetricsWriter:
    """
    Thread-safe, append-mode writer for ``metrics_summary.csv``.

    Each successful repository run writes one row immediately (and flushes
    to disk) so that a crash after N repos still leaves N rows persisted.
    The writer is safe to share across worker threads — ``write()`` holds
    an internal lock for the duration of the row write + flush.

    Usage::

        with IncrementalMetricsWriter(path) as writer:
            writer.write(record_dict)
    """

    def __init__(self, filepath: Path) -> None:
        self.filepath = filepath
        self._lock = threading.Lock()
        self._file = None
        self._writer: csv.DictWriter = None  # type: ignore[assignment]

    def __enter__(self) -> "IncrementalMetricsWriter":
        _ensure_output_dir(self.filepath.parent)
        is_new = not self.filepath.exists() or self.filepath.stat().st_size == 0
        self._file = open(self.filepath, "a", encoding="utf-8", newline="")
        self._writer = csv.DictWriter(
            self._file, fieldnames=METRICS_FIELDS, extrasaction="ignore"
        )
        if is_new:
            self._writer.writeheader()
            self._file.flush()
        return self

    def write(self, row: Dict) -> None:
        """Append *row* to the CSV under a lock and flush to disk."""
        with self._lock:
            self._writer.writerow(row)
            self._file.flush()

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._file is not None:
            self._file.close()
            self._file = None
            self._writer = None  # type: ignore[assignment]
