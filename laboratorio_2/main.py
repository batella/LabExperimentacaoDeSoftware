"""
Main automation script for Lab 02.

Pipeline:
  1. Fetch the top-1000 Java repositories from GitHub (GraphQL).
  2. Save the repository list to CSV.
  3. For each repository, clone it, run CK, and collect quality metrics.
     Processing runs in parallel via a ThreadPoolExecutor, writes one row
     to metrics_summary.csv as soon as it is available, and can be
     resumed after a crash.
  4. Leave analysis/visualisation to analysis.py.

Usage:
    python main.py [--limit N] [--workers N] [--keep-clones]
                   [--ck-only-first] [--no-resume]
"""

import argparse
import concurrent.futures as cf
from pathlib import Path
from typing import Dict, List, Optional

from config import Config
from github_client import GitHubClient
from repo_processor import normalise_repositories
from ck_runner import clone_and_run_ck
from ck_parser import summarise_ck_output
from exporter import (
    IncrementalMetricsWriter,
    load_processed_repos,
    save_repo_list,
)


DEFAULT_WORKERS = 4


def _build_arg_parser() -> argparse.ArgumentParser:
    """Return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Collect and analyse Java repository quality metrics."
    )
    parser.add_argument(
        "--limit", type=int, default=Config.REPOSITORIES_COUNT,
        help="Number of repositories to process (default: %(default)s)."
    )
    parser.add_argument(
        "--workers", type=int, default=DEFAULT_WORKERS,
        help="Parallel workers for clone+CK (default: %(default)s). "
             "Java+git are I/O and CPU heavy; 4-8 is a good range."
    )
    parser.add_argument(
        "--keep-clones", action="store_true",
        help="Keep local clones after CK analysis."
    )
    parser.add_argument(
        "--ck-only-first", action="store_true",
        help="Run CK only on the first repository (Sprint 1 demo)."
    )
    parser.add_argument(
        "--no-resume", action="store_true",
        help="Ignore any existing metrics_summary.csv and re-run every "
             "repository from scratch (default: resume mode on)."
    )
    return parser


def step_fetch_repositories(limit: int) -> List[Dict]:
    """Fetch and normalise repository data from GitHub."""
    print(f"[Step 1] Fetching top {limit} Java repositories from GitHub...")
    client = GitHubClient()
    raw_nodes = client.fetch_java_repositories(count=limit)
    repositories = normalise_repositories(raw_nodes)
    print(f"         Collected {len(repositories)} repositories.\n")
    return repositories


def step_save_repo_list(repositories: List[Dict]) -> Path:
    """Save the repository list CSV and return the file path."""
    output_path = Path(Config.OUTPUT_DIR) / Config.REPO_LIST_CSV
    saved = save_repo_list(repositories, output_path)
    print(f"[Step 2] Repository list saved to: {saved}\n")
    return saved


def _process_one_repo(
    repo: Dict,
    repos_base: Path,
    ck_base: Path,
    keep_clone: bool,
) -> Optional[Dict]:
    """
    Clone *repo*, run CK, parse output, return the enriched record.

    Returns None if the clone or CK step failed. This function is designed
    to be called from a worker thread; it does not share mutable state
    with other workers because each repo gets its own clone directory and
    CK output directory keyed by owner__name.
    """
    ck_output_dir = clone_and_run_ck(
        owner=repo["owner"],
        name=repo["name"],
        repos_base=repos_base,
        ck_base=ck_base,
        keep_clone=keep_clone,
    )
    if ck_output_dir is None:
        return None

    ck_summary = summarise_ck_output(ck_output_dir)
    return {**repo, **ck_summary}


def step_collect_metrics(
    repositories: List[Dict],
    keep_clones: bool,
    ck_only_first: bool,
    workers: int,
    resume: bool,
) -> None:
    """
    Clone repos, run CK, and stream results into metrics_summary.csv.

    Uses a ThreadPoolExecutor so that several clones + CK runs can
    proceed in parallel. Rows are written to the CSV as they arrive via
    an IncrementalMetricsWriter (locked + flushed per row), which means
    an interrupted run leaves a partial-but-valid CSV on disk and
    resume mode will pick up where it left off.
    """
    repos_base = Path(Config.REPOS_DIR)
    ck_base = Path(Config.OUTPUT_DIR) / "ck_results"
    metrics_path = Path(Config.OUTPUT_DIR) / Config.METRICS_CSV

    targets = repositories[:1] if ck_only_first else repositories

    processed: set = set()
    if resume:
        processed = load_processed_repos(metrics_path)
        if processed:
            before = len(targets)
            targets = [r for r in targets if r["full_name"] not in processed]
            print(f"[Step 3] Resume: {len(processed)} already processed, "
                  f"{before - len(targets)} skipped, {len(targets)} remaining.")

    total = len(targets)
    if total == 0:
        print("[Step 3] Nothing to do.\n")
        return

    word = "repository" if total == 1 else "repositories"
    print(f"[Step 3] Running CK on {total} {word} with {workers} worker(s)...")

    successes = 0
    failures = 0

    with IncrementalMetricsWriter(metrics_path) as writer:
        with cf.ThreadPoolExecutor(max_workers=workers) as pool:
            future_to_repo = {
                pool.submit(
                    _process_one_repo, repo, repos_base, ck_base, keep_clones
                ): repo
                for repo in targets
            }

            for idx, fut in enumerate(cf.as_completed(future_to_repo), start=1):
                repo = future_to_repo[fut]
                full_name = repo["full_name"]

                try:
                    record = fut.result()
                except Exception as exc:  # noqa: BLE001
                    print(f"  [{idx}/{total}] {full_name} EXCEPTION: {exc}")
                    failures += 1
                    continue

                if record is None:
                    print(f"  [{idx}/{total}] {full_name} skipped (clone/CK failed)")
                    failures += 1
                    continue

                writer.write(record)
                successes += 1
                print(
                    f"  [{idx}/{total}] {full_name} OK "
                    f"(classes={record['ck_class_count']}, "
                    f"loc={record['loc_total']})"
                )

    print(f"\n[Step 3] Done. {successes} succeeded, {failures} failed.\n")


def main() -> None:
    """Run the full data collection and metric analysis pipeline."""
    args = _build_arg_parser().parse_args()

    repositories = step_fetch_repositories(args.limit)
    step_save_repo_list(repositories)

    step_collect_metrics(
        repositories=repositories,
        keep_clones=args.keep_clones,
        ck_only_first=args.ck_only_first,
        workers=args.workers,
        resume=not args.no_resume,
    )

    print("All done. Run analysis.py next to generate descriptive stats and plots.")


if __name__ == "__main__":
    main()
