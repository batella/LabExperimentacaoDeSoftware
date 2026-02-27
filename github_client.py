"""GitHub API client for repository data collection."""

import requests
import time
from typing import List, Dict, Optional

from config import Config
from queries import GitHubQueries


class GitHubClient:
    """Client for interacting with GitHub GraphQL API."""
    
    def __init__(self):
        """Initialize GitHub client."""
        Config.validate()
        self.url = Config.GITHUB_API_URL
        self.headers = Config.get_headers()
        self.delay = Config.RATE_LIMIT_DELAY
    
    def _make_request(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """
        Make a GraphQL request to GitHub API.
        
        Args:
            query: GraphQL query string
            variables: Optional variables for the query
            
        Returns:
            Response data as dictionary
            
        Raises:
            requests.HTTPError: If request fails
        """
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        response = requests.post(self.url, json=payload, headers=self.headers)
        
        if response.status_code != 200:
            raise requests.HTTPError(
                f"Request failed with status {response.status_code}: {response.text}"
            )
        
        return response.json()
    
    def get_top_repositories(self, count: int = 100) -> List[Dict]:
        """
        Fetch list of top starred repositories.
        
        Args:
            count: Number of repositories to fetch (default: 100)
            
        Returns:
            List of repository basic info (name, owner)
        """
        data = self._make_request(GitHubQueries.SEARCH_TOP_REPOSITORIES)
        return data["data"]["search"]["nodes"]
    
    def get_repository_details(self, owner: str, name: str) -> Dict:
        """
        Fetch detailed information for a specific repository.
        
        Args:
            owner: Repository owner login
            name: Repository name
            
        Returns:
            Repository details dictionary
        """
        variables = {"owner": owner, "name": name}
        data = self._make_request(GitHubQueries.REPOSITORY_DETAILS, variables)
        return data["data"]["repository"]
    
    def fetch_all_repository_details(self, repositories: List[Dict]) -> List[Dict]:
        """
        Fetch details for all repositories with rate limiting.
        
        Args:
            repositories: List of repositories with owner and name
            
        Returns:
            List of repository details
        """
        results = []
        
        for i, repo in enumerate(repositories, 1):
            owner = repo["owner"]["login"]
            name = repo["name"]
            
            try:
                details = self.get_repository_details(owner, name)
                results.append(details)
                print(f"[{i}/{len(repositories)}] Fetched: {owner}/{name}")
            except requests.HTTPError as e:
                print(f"[{i}/{len(repositories)}] Error fetching {owner}/{name}: {e}")
            
            time.sleep(self.delay)
        
        return results
