"""
Main automation script for Lab 02 — data collection (Sprint 1).

At this stage the pipeline fetches the top-N Java repositories from
GitHub via the GraphQL API and saves their metadata to
``output/repositories_list.csv``. The CK analysis step and quality
metric collection will be added in the next sprint.

Usage:
    python main.py                 # fetches 1000 repos (the default)
    python main.py --limit 50      # fetches only 50 repos (useful for testing)
"""

import argparse
from pathlib import Path

from config import Config
from github_client import GitHubClient
from repo_processor import normalise_repositories
from exporter import save_repo_list


def _build_arg_parser() -> argparse.ArgumentParser:
    """Return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Collect top Java repositories from GitHub."
    )
    parser.add_argument(
        "--limit", type=int, default=Config.REPOSITORIES_COUNT,
        help="Number of repositories to fetch (default: %(default)s)."
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


def main() -> None:
    """Run the data collection pipeline."""
    args = _build_arg_parser().parse_args()

    repositories = step_fetch_repositories(args.limit)
    step_save_repo_list(repositories)

    print("Done. CK analysis and quality metrics will be added in the next sprint.")


if __name__ == "__main__":
    main()
