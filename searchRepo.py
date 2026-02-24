import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

url = "https://api.github.com/graphql"

headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json"
}

# 1️⃣ Buscar lista dos 100 mais estrelados
query_list = """
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

response = requests.post(url, json={"query": query_list}, headers=headers)

if response.status_code != 200:
    print("Erro ao buscar lista:", response.status_code)
    print(response.text)
    exit()

repos = response.json()["data"]["search"]["nodes"]

# 2️⃣ Query de detalhes
query_details = """
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    name
    createdAt
    updatedAt
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

for i, repo in enumerate(repos, 1):
    owner = repo["owner"]["login"]
    name = repo["name"]

    variables = {
        "owner": owner,
        "name": name
    }

    response = requests.post(
        url,
        json={"query": query_details, "variables": variables},
        headers=headers
    )

    if response.status_code == 200:
        data = response.json()
        print(f"{i}: {json.dumps(data['data']['repository'], indent=2)}")
    else:
        print(f"{i}: Erro ao buscar {name}: {response.status_code}")

    time.sleep(0.2)