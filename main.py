"""Main script for GitHub repository analysis - Lab01S01."""

import json
from typing import List, Dict

from github_client import GitHubClient
from data_processor import RepositoryMetrics
from data_exporter import DataExporter
from config import Config


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
        print("Step 4: Saving results to files...")
        output_json = DataExporter.save_to_json(processed_repos)
        print(f"JSON data saved to: {output_json}")
        
        # Save results to CSV file
        output_csv = DataExporter.save_to_csv(processed_repos)
        print(f"CSV data saved to: {output_csv}\n")
        
        # Display results
        print("="*80)
        print("RESULTS")
        print("="*80)
        display_repository_data(processed_repos)
        
        print(f"\n{'='*80}")
        print(f"Analysis complete: {len(processed_repos)} repositories processed")
        print(f"JSON file: {output_json}")
        print(f"CSV file: {output_csv}")
        print(f"{'='*80}")
        
    except Exception as e:
        print(f"\nError: {e}")
        raise


if __name__ == "__main__":
    main()
