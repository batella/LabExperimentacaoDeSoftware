"""Main script for GitHub repository analysis - Lab01S01."""

import json
import os
from typing import List, Dict
from datetime import datetime

from github_client import GitHubClient
from data_processor import RepositoryMetrics
from config import Config


def save_to_json(repositories: List[Dict], filename: str = None) -> str:
    """
    Save repository data to JSON file.
    
    Args:
        repositories: List of repository data
        filename: Output filename (optional, auto-generated if not provided)
        
    Returns:
        Path to saved file
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"repositories_{timestamp}.json"
    
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(repositories, f, indent=2, ensure_ascii=False)
    
    return filepath


def display_repository_data(repositories: List[Dict]) -> None:
    """
    Display processed repository data.
    
    Args:
        repositories: List of enriched repository data
    """
    for i, repo in enumerate(repositories, 1):
        print(f"\n{i}: {json.dumps(repo, indent=2)}")


def main():
    """Main execution function."""
    try:
        print("Starting GitHub repository analysis...")
        print(f"Fetching top {Config.REPOSITORIES_COUNT} repositories\n")
        
        # Initialize client
        client = GitHubClient()
        
        # Fetch list of top repositories
        print("Step 1: Fetching list of top repositories...")
        top_repos = client.get_top_repositories(Config.REPOSITORIES_COUNT)
        print(f"Found {len(top_repos)} repositories\n")
        
        # Fetch detailed data for each repository
        print("Step 2: Fetching detailed data for each repository...")
        detailed_repos = client.fetch_all_repository_details(top_repos)
        print(f"\nSuccessfully fetched details for {len(detailed_repos)} repositories\n")
        
        # Process and enrich data with calculated metrics
        print("Step 3: Processing data and calculating metrics...")
        processed_repos = RepositoryMetrics.process_repositories(detailed_repos)
        print(f"Processed {len(processed_repos)} repositories\n")
        
        # Save results to JSON file
        print("Step 4: Saving results to file...")
        output_file = save_to_json(processed_repos)
        print(f"Data saved to: {output_file}\n")
        
        # Display results
        print("="*80)
        print("RESULTS")
        print("="*80)
        display_repository_data(processed_repos)
        
        print(f"\n{'='*80}")
        print(f"Analysis complete: {len(processed_repos)} repositories processed")
        print(f"Results saved to: {output_file}")
        print(f"{'='*80}")
        
    except Exception as e:
        print(f"\nError: {e}")
        raise


if __name__ == "__main__":
    main()
