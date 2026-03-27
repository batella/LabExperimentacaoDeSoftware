"""
Main automation script for Lab 02 – Sprint 1.

Pipeline:
  1. Fetch the top-1000 Java repositories from GitHub.
  2. Save the repository list to CSV.
  3. For each repository, clone it, run CK, and collect quality metrics.
  4. Save the combined process + quality metrics to a second CSV.

Usage:
    python main.py [--limit N] [--keep-clones] [--ck-only-first]

Flags:
    --limit N          Process only the first N repositories (default: all 1000).
    --keep-clones      Do not delete clones after CK runs.
    --ck-only-first    Clone and run CK only on the first repository (Sprint 1 demo).
"""

import argparse
from pathlib import Path

from config import Config
from github_client import GitHubClient
from repo_processor import normalise_repositories
from ck_runner import clone_and_run_ck
from ck_parser import summarise_ck_output
from exporter import save_repo_list, save_metrics


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
        "--keep-clones", action="store_true",
        help="Keep local clones after CK analysis."
    )
    parser.add_argument(
        "--ck-only-first", action="store_true",
        help="Run CK only on the first repository (Sprint 1 demo)."
    )
    return parser


def step_fetch_repositories(limit: int):
    """Fetch and normalise repository data from GitHub."""
    print(f"[Step 1] Fetching top {limit} Java repositories from GitHub...")
    client = GitHubClient()
    raw_nodes = client.fetch_java_repositories(count=limit)
    repositories = normalise_repositories(raw_nodes)
    print(f"         Collected {len(repositories)} repositories.\n")
    return repositories


def step_save_repo_list(repositories: list) -> Path:
    """Save the repository list CSV and return the file path."""
    output_path = Path(Config.OUTPUT_DIR) / Config.REPO_LIST_CSV
    saved = save_repo_list(repositories, output_path)
    print(f"[Step 2] Repository list saved to: {saved}\n")
    return saved


def step_collect_metrics(repositories: list, keep_clones: bool, ck_only_first: bool) -> list:
    """Clone repositories, run CK, parse results, and return enriched records."""
    repos_base = Path(Config.REPOS_DIR)
    ck_base = Path(Config.OUTPUT_DIR) / "ck_results"

    targets = repositories[:1] if ck_only_first else repositories
    total = len(targets)

    print(f"[Step 3] Running CK on {total} repositor{'y' if total == 1 else 'ies'}...")

    enriched_records = []

    for idx, repo in enumerate(targets, start=1):
        owner, name = repo["owner"], repo["name"]
        print(f"  [{idx}/{total}] {owner}/{name}")

        ck_output_dir = clone_and_run_ck(
            owner=owner,
            name=name,
            repos_base=repos_base,
            ck_base=ck_base,
            keep_clone=keep_clones,
        )

        if ck_output_dir is None:
            continue

        ck_summary = summarise_ck_output(ck_output_dir)
        record = {**repo, **ck_summary}
        enriched_records.append(record)

    print(f"         Metrics collected for {len(enriched_records)} repositories.\n")
    return enriched_records


def step_save_metrics(records: list) -> Path:
    """Save the combined metrics CSV and return the file path."""
    output_path = Path(Config.OUTPUT_DIR) / Config.METRICS_CSV
    saved = save_metrics(records, output_path)
    print(f"[Step 4] Metrics summary saved to: {saved}\n")
    return saved


def main() -> None:
    """Run the full data collection and metric analysis pipeline."""
    args = _build_arg_parser().parse_args()

    repositories = step_fetch_repositories(args.limit)
    step_save_repo_list(repositories)

    metrics = step_collect_metrics(
        repositories=repositories,
        keep_clones=args.keep_clones,
        ck_only_first=args.ck_only_first,
    )

    if metrics:
        step_save_metrics(metrics)

    print("Done.")


if __name__ == "__main__":
    main()
