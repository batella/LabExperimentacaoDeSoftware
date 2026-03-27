"""Data processing and metrics calculation for repository analysis."""

from datetime import datetime, timezone
from typing import Dict, List


class RepositoryMetrics:
    """Calculate metrics for repository analysis."""
    
    @staticmethod
    def calculate_age_in_days(created_at: str) -> int:
        """
        Calculate repository age in days.
        
        Args:
            created_at: ISO format datetime string
            
        Returns:
            Age in days
        """
        created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        return (now - created).days
    
    @staticmethod
    def calculate_days_since_update(updated_at: str) -> int:
        """
        Calculate days since last update.
        
        Args:
            updated_at: ISO format datetime string
            
        Returns:
            Days since last update
        """
        updated = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        return (now - updated).days
    
    @staticmethod
    def calculate_days_since_push(pushed_at: str) -> int:
        """
        Calculate days since last push.
        
        Args:
            pushed_at: ISO format datetime string
            
        Returns:
            Days since last push
        """
        pushed = datetime.fromisoformat(pushed_at.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        return (now - pushed).days
    
    @staticmethod
    def calculate_closed_issues_ratio(total_issues: int, closed_issues: int) -> float:
        """
        Calculate ratio of closed issues.
        
        Args:
            total_issues: Total number of issues
            closed_issues: Number of closed issues
            
        Returns:
            Ratio of closed issues (0.0 to 1.0)
        """
        if total_issues == 0:
            return 0.0
        return round(closed_issues / total_issues, 2)
    
    @classmethod
    def enrich_repository_data(cls, repo_data: Dict) -> Dict:
        """
        Add calculated metrics to repository data.
        
        Args:
            repo_data: Raw repository data from API
            
        Returns:
            Enriched repository data with calculated metrics
        """
        enriched = repo_data.copy()
        
        enriched['ageInDays'] = cls.calculate_age_in_days(repo_data['createdAt'])
        enriched['daysSinceLastUpdate'] = cls.calculate_days_since_update(
            repo_data['updatedAt']
        )
        enriched['daysSinceLastPush'] = cls.calculate_days_since_push(
            repo_data['pushedAt']
        )
        enriched['closedIssuesRatio'] = cls.calculate_closed_issues_ratio(
            repo_data['issues']['totalCount'],
            repo_data['closedIssues']['totalCount']
        )
        
        return enriched
    
    @classmethod
    def process_repositories(cls, repositories: List[Dict]) -> List[Dict]:
        """
        Process list of repositories and add calculated metrics.
        
        Args:
            repositories: List of raw repository data
            
        Returns:
            List of enriched repository data
        """
        return [cls.enrich_repository_data(repo) for repo in repositories]
