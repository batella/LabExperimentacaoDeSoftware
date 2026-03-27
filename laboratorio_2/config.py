"""Configuration constants for the Java quality analysis lab."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application-wide configuration."""

    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    GITHUB_API_URL = "https://api.github.com/graphql"

    REPOSITORIES_COUNT = 1000
    PAGE_SIZE = 50
    RATE_LIMIT_DELAY = 0.5

    REPOS_DIR = "repos"
    OUTPUT_DIR = "output"
    CK_JAR_PATH = os.getenv("CK_JAR_PATH", "ck.jar")

    CK_CLASS_FILE = "class.csv"

    REPO_LIST_CSV = "repositories_list.csv"
    METRICS_CSV = "metrics_summary.csv"

    @classmethod
    def get_headers(cls) -> dict:
        """Return HTTP headers for GitHub API requests."""
        return {
            "Authorization": f"Bearer {cls.GITHUB_TOKEN}",
            "Content-Type": "application/json",
        }

    @classmethod
    def validate(cls) -> None:
        """Raise ValueError if required environment variables are missing."""
        if not cls.GITHUB_TOKEN:
            raise ValueError("GITHUB_TOKEN not found in environment variables")
