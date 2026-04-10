"""GitHub GraphQL API client for repository data collection."""

import random
import time
from typing import Dict, List, Optional

import requests

from config import Config
from queries import GitHubQueries

# Retry policy for transient GitHub/upstream failures.
# Exponential backoff with full jitter: wait ~= random(0, base * 2**attempt)
# capped at _RETRY_BACKOFF_MAX. This is kinder to the edge when it's
# already struggling (bunched retries at fixed intervals make 502s worse).
_RETRY_ATTEMPTS = 6
_RETRY_BACKOFF_BASE = 2
_RETRY_BACKOFF_MAX = 60
_RETRYABLE_STATUS = {500, 502, 503, 504, 408, 429}


def _compute_backoff(attempt: int) -> float:
    """
    Compute a backoff duration in seconds for *attempt* (1-indexed) with
    exponential growth and full jitter, capped at _RETRY_BACKOFF_MAX.
    """
    upper = min(_RETRY_BACKOFF_BASE * (2 ** attempt), _RETRY_BACKOFF_MAX)
    return random.uniform(0, upper)


class GitHubClient:
    """Client for interacting with the GitHub GraphQL API."""

    def __init__(self) -> None:
        """Initialise the client and validate configuration."""
        Config.validate()
        self.url = Config.GITHUB_API_URL
        self.headers = Config.get_headers()
        self.delay = Config.RATE_LIMIT_DELAY

    def _post(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """
        Send a GraphQL request and return the parsed JSON body.

        Retries on transient HTTP codes (500, 502, 503, 504, 408, 429)
        and on network-level exceptions, with exponential backoff +
        full jitter capped at _RETRY_BACKOFF_MAX. Raises
        :class:`requests.HTTPError` or the original network exception
        once _RETRY_ATTEMPTS is exhausted.
        """
        payload: Dict = {"query": query}
        if variables:
            payload["variables"] = variables

        last_exc: Optional[Exception] = None
        last_status: Optional[int] = None
        last_body: str = ""

        for attempt in range(1, _RETRY_ATTEMPTS + 1):
            try:
                response = requests.post(
                    self.url, json=payload, headers=self.headers, timeout=30
                )
            except (requests.ConnectionError, requests.Timeout) as exc:
                last_exc = exc
                last_status = None
                if attempt < _RETRY_ATTEMPTS:
                    wait = _compute_backoff(attempt)
                    print(f"\n  [WARN] network error on attempt "
                          f"{attempt}/{_RETRY_ATTEMPTS}: {exc}. "
                          f"Retrying in {wait:.1f}s...")
                    time.sleep(wait)
                    continue
                raise

            if response.status_code == 200:
                return response.json()

            last_status = response.status_code
            last_body = response.text

            if response.status_code in _RETRYABLE_STATUS and attempt < _RETRY_ATTEMPTS:
                wait = _compute_backoff(attempt)
                print(f"\n  [WARN] HTTP {response.status_code} on attempt "
                      f"{attempt}/{_RETRY_ATTEMPTS}. Retrying in {wait:.1f}s...")
                time.sleep(wait)
                continue

            raise requests.HTTPError(
                f"GitHub API returned {response.status_code}: {response.text[:500]}"
            )

        # Exhausted retries on network errors
        if last_exc is not None:
            raise last_exc
        raise requests.HTTPError(
            f"GitHub API returned {last_status}: {last_body[:500]}"
        )

    def _unwrap_search(self, data: Dict) -> Dict:
        """Return the 'search' node from a GraphQL response."""
        return data["data"]["search"]

    def fetch_java_repositories(self, count: int = Config.REPOSITORIES_COUNT) -> List[Dict]:
        """
        Fetch the top Java repositories ordered by star count.

        Uses cursor-based pagination to collect up to *count* repositories.
        Returns a list of raw repository nodes from the API.
        """
        repositories: List[Dict] = []
        cursor: Optional[str] = None

        while len(repositories) < count:
            variables = {"cursor": cursor} if cursor else {}
            data = self._post(GitHubQueries.SEARCH_JAVA_REPOSITORIES_PAGINATED, variables)
            search = self._unwrap_search(data)

            repositories.extend(search["nodes"])
            print(f"Collected {min(len(repositories), count)}/{count} repositories...", end="\r")

            page_info = search["pageInfo"]
            if not page_info["hasNextPage"]:
                break

            cursor = page_info["endCursor"]
            time.sleep(self.delay)

        print()
        return repositories[:count]
