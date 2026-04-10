"""GraphQL query templates for GitHub API."""


class GitHubQueries:
    """Collection of GraphQL queries used to retrieve Java repository data."""

    SEARCH_JAVA_REPOSITORIES_PAGINATED = """
    query($cursor: String) {
      search(
        query: "language:Java stars:>1 sort:stars-desc"
        type: REPOSITORY
        first: 50
        after: $cursor
      ) {
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          ... on Repository {
            name
            owner { login }
            url
            createdAt
            stargazerCount
            releases { totalCount }
            primaryLanguage { name }
            defaultBranchRef { name }
          }
        }
      }
    }
    """
