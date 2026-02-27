"""GraphQL query templates for GitHub API."""


class GitHubQueries:
    """Collection of GraphQL queries for GitHub data retrieval."""
    
    SEARCH_TOP_REPOSITORIES = """
    query {
      search(
        query: "stars:>1 sort:stars-desc"
        type: REPOSITORY
        first: 100
      ) {
        nodes {
          ... on Repository {
            name
            owner {
              login
            }
          }
        }
      }
    }
    """
    
    REPOSITORY_DETAILS = """
    query($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) {
        name
        createdAt
        updatedAt
        pushedAt
        stargazerCount
        
        primaryLanguage {
          name
        }

        releases {
          totalCount
        }

        issues {
          totalCount
        }

        closedIssues: issues(states: CLOSED) {
          totalCount
        }

        pullRequests(states: MERGED) {
          totalCount
        }
      }
    }
    """
