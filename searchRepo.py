import requests
import json
import os
import time
from datetime import datetime, timezone
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
        repo_data = data['data']['repository']
        
        # Calcular idade do repositório
        created_at = datetime.fromisoformat(repo_data['createdAt'].replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        age_days = (now - created_at).days
        
        # Calcular tempo desde última atualização
        updated_at = datetime.fromisoformat(repo_data['updatedAt'].replace('Z', '+00:00'))
        days_since_update = (now - updated_at).days
        
        # Calcular tempo desde último push
        pushed_at = datetime.fromisoformat(repo_data['pushedAt'].replace('Z', '+00:00'))
        days_since_push = (now - pushed_at).days
        
        # Calcular razão de issues fechadas
        total_issues = repo_data['issues']['totalCount']
        closed_issues = repo_data['closedIssues']['totalCount']
        closed_ratio = closed_issues / total_issues if total_issues > 0 else 0
        
        # Adicionar campos calculados
        repo_data['ageInDays'] = age_days
        repo_data['daysSinceLastUpdate'] = days_since_update
        repo_data['daysSinceLastPush'] = days_since_push
        repo_data['closedIssuesRatio'] = round(closed_ratio, 2)
        
        print(f"{i}: {json.dumps(repo_data, indent=2)}")
    else:
        print(f"{i}: Erro ao buscar {name}: {response.status_code}")

    time.sleep(0.2)