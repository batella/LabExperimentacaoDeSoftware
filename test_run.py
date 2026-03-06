"""Quick test to verify the setup works."""

from config import Config
from github_client import GitHubClient
from data_processor import RepositoryMetrics

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)

def print_section(text):
    """Print a section separator."""
    print(f"\n{'─' * 80}")
    print(f"► {text}")
    print('─' * 80)

def print_repo_details(i, repo, details):
    """Print detailed repository information."""
    print(f"\n[{i}] {repo['owner']['login']}/{repo['name']}")
    print(f"Stars: {details['stargazerCount']:,}")
    print(f"Created: {details['createdAt'][:10]} ({details['ageInDays']} days old)")
    print(f"Last update: {details['daysSinceLastUpdate']} days ago")
    print(f"Last push: {details['daysSinceLastPush']} days ago")
    print(f"Language: {details['primaryLanguage']['name'] if details['primaryLanguage'] else 'N/A'}")
    print(f"Merged PRs: {details['pullRequests']['totalCount']}")
    print(f"Releases: {details['releases']['totalCount']}")
    print(f"Issues: {details['closedIssues']['totalCount']}/{details['issues']['totalCount']} closed ({details['closedIssuesRatio']*100:.0f}%)")

# Main test
print_header("GitHub Repository Analysis - Test Run")

print("\n[1/4] Checking configuration...")
print(f"      ✓ Token loaded: {'Yes' if Config.GITHUB_TOKEN else 'No'}")
if Config.GITHUB_TOKEN:
    print(f"      ✓ Token prefix: {Config.GITHUB_TOKEN[:10]}...")
    print(f"      ✓ API URL: {Config.GITHUB_API_URL}")
else:
    print("\nERROR: Please configure GITHUB_TOKEN in .env file")
    exit(1)

print("\n[2/4] Initializing GitHub client...")
try:
    client = GitHubClient()
    print("      ✓ Client initialized successfully")
except Exception as e:
    print(f"Error: {e}")
    exit(1)

print("\n[3/4] Fetching top 5 repositories (test query)...")
try:
    repos = client.get_top_repositories(5)
    print(f"      ✓ Successfully fetched {len(repos)} repositories")
except Exception as e:
    print(f"Error: {e}")
    exit(1)

print("\n[4/4] Fetching detailed data and calculating metrics...")
print_section("REPOSITORY DETAILS")

for i, repo in enumerate(repos, 1):
    owner = repo['owner']['login']
    name = repo['name']
    
    try:
        print(f"\n    Fetching: {owner}/{name}...", end=" ")
        details = client.get_repository_details(owner, name)
        enriched = RepositoryMetrics.enrich_repository_data(details)
        print("✓")
        print_repo_details(i, repo, enriched)
    except Exception as e:
        print(f"Error: {e}")

print_header("✅ Test completed successfully!")
print("\nYou can now run the full analysis")
print()
