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
from typing import Dict, List, Optional, Tuple

from config import Config
from github_client import GitHubClient
from repo_processor import normalise_repositories
from ck_runner import clone_and_run_ck
from ck_parser import summarise_ck_output
from exporter import (
    IncrementalFailureWriter,
    IncrementalMetricsWriter,
    load_failed_repos,
    load_processed_repos,
    load_repo_list,
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
    parser.add_argument(
        "--retry-failed", action="store_true",
        help="Retry repositories previously logged in failures.csv "
             "(by default they are skipped along with already-processed ones)."
    )
    parser.add_argument(
        "--refresh-repo-list", action="store_true",
        help="Force a fresh GitHub GraphQL fetch even if "
             "repositories_list.csv already exists (default: reuse cached list)."
    )
    return parser


def step_fetch_repositories(limit: int, refresh: bool = False) -> List[Dict]:
    """
    Return the list of target repositories, using the on-disk cache when
    possible.

    If ``output/repositories_list.csv`` already contains at least *limit*
    rows and *refresh* is False, the cached file is loaded straight from
    disk and no GitHub request is made. This avoids re-doing 20 GraphQL
    requests (and surviving an upstream 5xx) every time the user
    restarts the pipeline.

    Pass ``--refresh-repo-list`` from the CLI to force a fresh fetch.
    """
    output_path = Path(Config.OUTPUT_DIR) / Config.REPO_LIST_CSV

    if not refresh and output_path.is_file():
        cached = load_repo_list(output_path)
        if len(cached) >= limit:
            print(
                f"[Step 1] Using cached repository list from {output_path} "
                f"({len(cached)} repos; requested limit {limit}).\n"
            )
            return cached[:limit]
        else:
            print(
                f"[Step 1] Cached list has only {len(cached)} rows "
                f"(need {limit}); fetching fresh data from GitHub."
            )

    print(f"[Step 1] Fetching top {limit} Java repositories from GitHub...")
    client = GitHubClient()
    raw_nodes = client.fetch_java_repositories(count=limit)
    repositories = normalise_repositories(raw_nodes)
    print(f"         Collected {len(repositories)} repositories.\n")
    return repositories


def step_save_repo_list(repositories: List[Dict]) -> Path:
    """Save the repository list CSV and return the file path.

    Safe to call unconditionally: if the list came from the on-disk cache,
    re-writing it is a no-op, and if it was freshly fetched we want it
    persisted so the next run can reuse it.
    """
    output_path = Path(Config.OUTPUT_DIR) / Config.REPO_LIST_CSV
    saved = save_repo_list(repositories, output_path)
    print(f"[Step 2] Repository list saved to: {saved}\n")
    return saved


def _process_one_repo(
    repo: Dict,
    repos_base: Path,
    ck_base: Path,
    keep_clone: bool,
) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Clone *repo*, run CK, parse output, return (record, error_reason).

    On success returns (record_dict, None). On failure returns
    (None, "human-readable reason"). The function is thread-safe: each
    repo gets its own clone directory and CK output directory keyed by
    owner__name, so workers do not share mutable state.
    """
    ck_output_dir, error_reason = clone_and_run_ck(
        owner=repo["owner"],
        name=repo["name"],
        repos_base=repos_base,
        ck_base=ck_base,
        keep_clone=keep_clone,
    )
    if ck_output_dir is None:
        return None, error_reason

    ck_summary = summarise_ck_output(ck_output_dir)
    return {**repo, **ck_summary}, None


def step_collect_metrics(
    repositories: List[Dict],
    keep_clones: bool,
    ck_only_first: bool,
    workers: int,
    resume: bool,
    retry_failed: bool,
) -> None:
    """
    Clone repos, run CK, and stream results into metrics_summary.csv.

    Uses a ThreadPoolExecutor so that several clones + CK runs can
    proceed in parallel. Successful rows are appended to metrics_summary.csv
    and failed rows (with reason + timestamp) to failures.csv; both writers
    flush to disk per row so an interrupted run leaves a complete audit
    trail of everything attempted so far. On the next run, resume mode
    skips anything in either CSV unless --retry-failed is passed.
    """
    repos_base = Path(Config.REPOS_DIR)
    ck_base = Path(Config.OUTPUT_DIR) / "ck_results"
    metrics_path = Path(Config.OUTPUT_DIR) / Config.METRICS_CSV
    failures_path = Path(Config.OUTPUT_DIR) / Config.FAILURES_CSV

    targets = repositories[:1] if ck_only_first else repositories

    processed: set = set()
    previously_failed: set = set()
    if resume:
        processed = load_processed_repos(metrics_path)
        previously_failed = load_failed_repos(failures_path)
        if processed or previously_failed:
            before = len(targets)
            skip_set = set(processed)
            if not retry_failed:
                skip_set |= previously_failed
            targets = [r for r in targets if r["full_name"] not in skip_set]
            skipped = before - len(targets)
            parts = [f"{len(processed)} already processed"]
            if previously_failed:
                parts.append(
                    f"{len(previously_failed)} previously failed "
                    f"({'retrying' if retry_failed else 'skipping'})"
                )
            print(f"[Step 3] Resume: {', '.join(parts)}, "
                  f"{skipped} skipped, {len(targets)} remaining.")

    total = len(targets)
    if total == 0:
        print("[Step 3] Nothing to do.\n")
        return

    word = "repository" if total == 1 else "repositories"
    print(f"[Step 3] Running CK on {total} {word} with {workers} worker(s)...")

    successes = 0
    failures = 0

    with IncrementalMetricsWriter(metrics_path) as writer, \
         IncrementalFailureWriter(failures_path) as failure_writer:
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
                    record, reason = fut.result()
                except Exception as exc:  # noqa: BLE001
                    reason = f"unhandled exception: {type(exc).__name__}: {exc}"
                    print(f"  [{idx}/{total}] {full_name} EXCEPTION: {reason}")
                    failure_writer.write(full_name, reason)
                    failures += 1
                    continue

                if record is None:
                    print(f"  [{idx}/{total}] {full_name} FAILED: {reason}")
                    failure_writer.write(full_name, reason or "unknown")
                    failures += 1
                    continue

                writer.write(record)
                successes += 1
                print(
                    f"  [{idx}/{total}] {full_name} OK "
                    f"(classes={record['ck_class_count']}, "
                    f"loc={record['loc_total']})"
                )

    print(f"\n[Step 3] Done. {successes} succeeded, {failures} failed.")
    if failures:
        print(f"         Failure details: {failures_path}")
    print()


def main() -> None:
    """Run the full data collection and metric analysis pipeline."""
    args = _build_arg_parser().parse_args()

    repositories = step_fetch_repositories(
        args.limit, refresh=args.refresh_repo_list
    )
    step_save_repo_list(repositories)

    step_collect_metrics(
        repositories=repositories,
        keep_clones=args.keep_clones,
        ck_only_first=args.ck_only_first,
        workers=args.workers,
        resume=not args.no_resume,
        retry_failed=args.retry_failed,
    )

    print("All done. Run analysis.py next to generate descriptive stats and plots.")


if __name__ == "__main__":
    main()
