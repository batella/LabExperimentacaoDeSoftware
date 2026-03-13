# Análise de Repositório GitHub - Lab01S01

## Estrutura do Projeto

```
├── config.py           # Configuração e variáveis de ambiente
├── queries.py          # Modelos de consulta GraphQL
├── github_client.py    # Implementação do cliente da API GitHub
├── data_processor.py   # Cálculo de métricas e processamento de dados
├── main.py            # Script principal de orquestração
└── README.md          # Este arquivo
```

## Recursos

- **Design Modular**: Separação limpa de responsabilidades em vários módulos
- **Dicas de Tipo**: Anotações de tipo completas para melhor clareza do código e suporte ao IDE
- **Tratamento de Erros**: Tratamento abrangente de erros e validação
- **Limitação de Taxa**: Atraso integrado entre solicitações para respeitar limites da API
- **Extensível**: Fácil de adicionar novas consultas e métricas

## Configuração

### Opção 1: Docker (Recomendado)

1. Crie um arquivo `.env` com seu token do GitHub:
```bash
cp .env.example .env
# Edite .env e adicione seu token
```

2. Execute com um único comando:
```bash
docker-compose up
```

### Opção 2: Python Local

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

2. Crie um arquivo `.env` com seu token do GitHub:
```
GITHUB_TOKEN=seu_token_github_aqui
```

3. Execute o script:
```bash
python main.py
```

## Métricas Coletadas (Lab01S01)

O script coleta dados para responder às seguintes perguntas de pesquisa:

- **RQ01**: Idade do repositório (calculada a partir da data de criação)
- **RQ02**: Total de pull requests mesclados
- **RQ03**: Total de releases
- **RQ04**: Dias desde a última atualização
- **RQ05**: Linguagem de programação principal
- **RQ06**: Razão de issues fechadas (fechadas/total)

## Descrição dos Módulos

### config.py
Contém configuração da aplicação incluindo:
- Credenciais da API GitHub
- Endpoints da API
- Parâmetros de consulta
- Configurações de limitação de taxa

### queries.py
Modelos de consulta GraphQL:
- `SEARCH_TOP_REPOSITORIES`: Obter lista de repositórios mais estrelados
- `REPOSITORY_DETAILS`: Obter métricas detalhadas para um único repositório

### github_client.py
Cliente da API com métodos:
- `get_top_repositories()`: Buscar lista de repositórios principais
- `get_repository_details()`: Buscar dados de um único repositório
- `fetch_all_repository_details()`: Busca em lote com limitação de taxa

### data_processor.py
Cálculo de métricas:
- `calculate_age_in_days()`: Idade do repositório
- `calculate_days_since_update()`: Tempo desde a última atualização
- `calculate_days_since_push()`: Tempo desde o último push
- `calculate_closed_issues_ratio()`: Razão de issues fechadas
- `enrich_repository_data()`: Adicionar todas as métricas calculadas
- `process_repositories()`: Processamento em lote

### main.py
Orquestração principal:
1. Buscar lista dos 100 repositórios principais
2. Buscar dados detalhados para cada repositório
3. Calcular métricas e enriquecer dados
4. Exibir resultados
