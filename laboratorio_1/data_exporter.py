"""Data export utilities for repository analysis."""

import json
import csv
import os
from typing import List, Dict
from datetime import datetime


class DataExporter:
    """Handle data export to different file formats."""
    
    @staticmethod
    def save_to_json(repositories: List[Dict], filename: str = None) -> str:
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"repositories_{timestamp}.json"
        
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(repositories, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    @staticmethod
    def save_to_csv(repositories: List[Dict], filename: str = None) -> str:
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"repositories_{timestamp}.csv"
        
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        
        if not repositories:
            return filepath
        
        # Define CSV headers based on the data structure
        fieldnames = [
            'name',
            'createdAt',
            'updatedAt',
            'pushedAt',
            'stargazerCount',
            'primaryLanguage',
            'releasesCount',
            'issuesCount',
            'closedIssuesCount',
            'mergedPullRequestsCount',
            'ageInDays',
            'daysSinceLastUpdate',
            'daysSinceLastPush',
            'closedIssuesRatio'
        ]
        
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for repo in repositories:
                row = {
                    'name': repo.get('name', ''),
                    'createdAt': repo.get('createdAt', ''),
                    'updatedAt': repo.get('updatedAt', ''),
                    'pushedAt': repo.get('pushedAt', ''),
                    'stargazerCount': repo.get('stargazerCount', 0),
                    'primaryLanguage': repo.get('primaryLanguage', {}).get('name', '') if repo.get('primaryLanguage') else '',
                    'releasesCount': repo.get('releases', {}).get('totalCount', 0),
                    'issuesCount': repo.get('issues', {}).get('totalCount', 0),
                    'closedIssuesCount': repo.get('closedIssues', {}).get('totalCount', 0),
                    'mergedPullRequestsCount': repo.get('pullRequests', {}).get('totalCount', 0),
                    'ageInDays': repo.get('ageInDays', 0),
                    'daysSinceLastUpdate': repo.get('daysSinceLastUpdate', 0),
                    'daysSinceLastPush': repo.get('daysSinceLastPush', 0),
                    'closedIssuesRatio': repo.get('closedIssuesRatio', 0.0)
                }
                writer.writerow(row)
        
        return filepath
