"""Configuration module for GitHub repository analysis."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""
    
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    GITHUB_API_URL = "https://api.github.com/graphql"
    
    # Query parameters
    REPOSITORIES_COUNT = 100
    RATE_LIMIT_DELAY = 0.2  # seconds between requests
    
    # Headers for API requests
    @classmethod
    def get_headers(cls):
        """Return headers for GitHub API requests."""
        return {
            "Authorization": f"Bearer {cls.GITHUB_TOKEN}",
            "Content-Type": "application/json"
        }
    
    @classmethod
    def validate(cls):
        """Validate required configuration."""
        if not cls.GITHUB_TOKEN:
            raise ValueError("GITHUB_TOKEN not found in environment variables")
