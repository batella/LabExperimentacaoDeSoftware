"""Normalise raw GitHub GraphQL repository nodes into flat dictionaries."""

from datetime import datetime, timezone
from typing import Dict, List, Optional


def _parse_iso(timestamp: Optional[str]) -> Optional[datetime]:
    """Return a timezone-aware datetime for an ISO-8601 string, or None."""
    if not timestamp:
        return None
    # GitHub returns values like "2014-05-03T21:12:34Z"
    return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))


def _age_in_years(created_at: Optional[datetime]) -> float:
    """Compute the repository age in years from *created_at* to now (UTC)."""
    if created_at is None:
        return 0.0
    now = datetime.now(timezone.utc)
    delta_days = (now - created_at).days
    return round(delta_days / 365.25, 2)


def normalise_repository(node: Dict) -> Dict:
    """
    Flatten a single raw repository node into a simple dict.

    Returns fields needed by the exporter and downstream analysis:
    owner, name, full_name, url, stars, releases, age_years, created_at,
    primary_language, default_branch.
    """
    owner = node.get("owner", {}).get("login", "")
    name = node.get("name", "")
    created_at_raw = node.get("createdAt")
    created_at_dt = _parse_iso(created_at_raw)

    releases_node = node.get("releases") or {}
    primary_language_node = node.get("primaryLanguage") or {}
    default_branch_node = node.get("defaultBranchRef") or {}

    return {
        "owner": owner,
        "name": name,
        "full_name": f"{owner}/{name}",
        "url": node.get("url", ""),
        "stars": node.get("stargazerCount", 0),
        "releases": releases_node.get("totalCount", 0),
        "age_years": _age_in_years(created_at_dt),
        "created_at": created_at_raw or "",
        "primary_language": primary_language_node.get("name", ""),
        "default_branch": default_branch_node.get("name", ""),
    }


def normalise_repositories(nodes: List[Dict]) -> List[Dict]:
    """Normalise a list of raw repository nodes, skipping empty entries."""
    return [normalise_repository(node) for node in nodes if node]
