"""GitHub GraphQL API client for repository data collection."""

import time
from typing import Dict, List, Optional

import requests

from config import Config
from queries import GitHubQueries

_RETRY_ATTEMPTS = 3
_RETRY_BACKOFF_BASE = 5


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

        Retries up to _RETRY_ATTEMPTS times with exponential backoff on 5xx
        responses. Raises requests.HTTPError if all attempts fail.
        """
        payload: Dict = {"query": query}
        if variables:
            payload["variables"] = variables

        for attempt in range(1, _RETRY_ATTEMPTS + 1):
            response = requests.post(self.url, json=payload, headers=self.headers, timeout=30)

            if response.status_code == 200:
                return response.json()

            is_transient = response.status_code >= 500
            if is_transient and attempt < _RETRY_ATTEMPTS:
                wait = _RETRY_BACKOFF_BASE * attempt
                print(f"\n  [WARN] {response.status_code} on attempt {attempt}/{_RETRY_ATTEMPTS}. Retrying in {wait}s...")
                time.sleep(wait)
                continue

            raise requests.HTTPError(
                f"GitHub API returned {response.status_code}: {response.text}"
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
