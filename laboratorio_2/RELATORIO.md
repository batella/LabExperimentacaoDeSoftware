# Laboratório 02 — Um estudo das características de qualidade de sistemas Java

**Disciplina:** Laboratório de Experimentação de Software
**Curso:** Engenharia de Software — PUC Minas
**Período:** 6º
**Professor:** João Paulo Carneiro Aramuni

---

## 1. Introdução

No processo de desenvolvimento colaborativo de software open-source, em que
diversos desenvolvedores contribuem em partes diferentes do código, atributos
de qualidade interna como modularidade, manutenibilidade e coesão estão sob
pressão constante. Este estudo analisa os **top-1.000 repositórios Java mais
populares do GitHub**, calculando métricas de qualidade através da ferramenta
[CK](https://github.com/mauricioaniche/ck) e correlacionando-as com
características de processo dos repositórios.

### 1.1. Questões de Pesquisa

- **RQ01.** Qual a relação entre a **popularidade** dos repositórios e as suas
  características de qualidade?
- **RQ02.** Qual a relação entre a **maturidade** dos repositórios e as suas
  características de qualidade?
- **RQ03.** Qual a relação entre a **atividade** dos repositórios e as suas
  características de qualidade?
- **RQ04.** Qual a relação entre o **tamanho** dos repositórios e as suas
  características de qualidade?

### 1.2. Hipóteses Informais

Antes de realizar a análise, elaboramos as seguintes expectativas sobre os
resultados, que serão comparadas com os valores obtidos na Seção 4
(Discussão).

- **H-RQ01 (popularidade × qualidade).** Repositórios mais populares tendem a
  apresentar melhor qualidade interna, pois atraem contribuidores mais
  experientes, recebem revisões de código mais rigorosas e enfrentam maior
  pressão pública por clareza. Esperamos **correlação negativa fraca** entre
  número de estrelas e CBO/LCOM (mais estrelas → menor acoplamento, maior
  coesão) e correlação quase nula com DIT, já que profundidade de herança é
  mais um estilo arquitetural do que consequência de popularidade.

- **H-RQ02 (maturidade × qualidade).** Projetos mais antigos acumulam código
  legado, refatorações inconsistentes e padrões de Java pré-2010 (uso mais
  agressivo de herança em vez de composição). Esperamos **correlação positiva
  fraca a moderada** entre idade do repositório e CBO/LCOM, e correlação
  positiva também com DIT, já que hierarquias mais profundas eram comuns em
  código Java antigo.

- **H-RQ03 (atividade × qualidade).** Repositórios com mais releases
  pressupõem manutenção ativa, CI/CD e disciplina de código, incluindo
  refatoração contínua. Esperamos **correlação negativa fraca** entre
  número de releases e CBO/LCOM. Para DIT a expectativa é de correlação
  quase nula, já que a estrutura de herança geralmente é estabelecida cedo e
  raramente muda durante a vida útil do projeto.

- **H-RQ04 (tamanho × qualidade).** Repositórios maiores carregam mais
  complexidade inerente, mais dependências entre módulos e mais chance de
  terem "god classes". Esperamos **correlação positiva moderada** entre LOC
  total e CBO, e também positiva com LCOM (mais código → classes maiores →
  menor coesão). Para DIT esperamos correlação fraca-positiva, já que
  projetos maiores tendem a desenvolver hierarquias de tipos mais extensas.

---

## 2. Metodologia

### 2.1. Seleção dos repositórios

Coletamos os 1.000 repositórios Java mais populares do GitHub via a
**API GraphQL v4**, usando o query `language:Java sort:stars-desc`. Para cada
repositório armazenamos: nome, proprietário, URL, número de estrelas,
`createdAt`, contagem de releases, linguagem primária e branch default. A
idade do repositório é calculada como `(hoje − createdAt)` em anos.

### 2.2. Definição das métricas

#### Métricas de processo

| Métrica | Definição | Fonte |
|---|---|---|
| Popularidade | Número de stargazers | GitHub GraphQL (`stargazerCount`) |
| Maturidade | Anos desde a criação do repositório | GitHub GraphQL (`createdAt`) |
| Atividade | Número total de releases publicadas | GitHub GraphQL (`releases.totalCount`) |
| Tamanho | Soma das LOC de todas as classes analisadas por CK | CK (`class.csv`, coluna `loc`) |

#### Métricas de qualidade

Extraídas da ferramenta **CK** sobre o código-fonte de cada repositório:

| Métrica | Significado |
|---|---|
| **CBO** (Coupling Between Objects) | Número de classes das quais a classe depende |
| **DIT** (Depth of Inheritance Tree) | Profundidade da classe na árvore de herança |
| **LCOM** (Lack of Cohesion of Methods) | Ausência de coesão entre os métodos da classe |

### 2.3. Pipeline de coleta

1. **Busca** dos 1.000 repositórios via GraphQL, com paginação por cursor
   (50 por página, 20 requisições). Dados normalizados em
   `output/repositories_list.csv`.
2. **Clone e análise** em paralelo, via `ThreadPoolExecutor` com N workers
   (default 4). Cada worker executa, para um repositório:
   - `git clone --depth 1 <owner>/<name>`
   - `java -jar ck.jar <clone> false 0 false <outdir>/`
   - Parse do `class.csv` e sumarização por repositório
   - Remoção do clone após conclusão (ou em caso de falha)
3. **Escrita incremental** em `output/metrics_summary.csv` via um writer
   thread-safe que faz `flush()` após cada linha, garantindo que uma
   interrupção não perca o progresso já coletado.
4. **Retomada** automática: antes de processar, o pipeline lê o CSV
   existente e pula repositórios já presentes.

### 2.4. Sumarização por repositório

CK produz um arquivo `class.csv` com uma linha por classe (incluindo classes
internas, anônimas, interfaces e enums). Para cada repositório calculamos,
sobre todas as classes:

- `CBO_mean`, `CBO_median`, `CBO_stdev`
- `DIT_mean`, `DIT_median`, `DIT_stdev`
- `LCOM_mean`, `LCOM_median`, `LCOM_stdev`
- `loc_total` (soma de LOC das classes — métrica de Size para RQ04)
- `loc_mean`, `loc_median`, `loc_stdev`

O relatório utiliza como **métrica central para as correlações a mediana**,
não a média. Ver justificativa em §2.5.

### 2.5. Decisões metodológicas

Três escolhas merecem ser explicitadas porque afetam a interpretação dos
resultados:

1. **Mediana em vez de média para LCOM.** Durante a validação do pipeline,
   observamos que classes de teste de grandes projetos (por exemplo,
   `JsonReaderTest` em `google/gson`, com 158 métodos e LCOM=12403) dominam
   completamente a média repo-level. A mediana representa a classe típica
   de forma muito mais robusta a outliers e é o resumo adotado por estudos
   empíricos similares. Usamos mediana também para CBO e DIT por consistência.

2. **Inclusão de classes de teste.** CK não distingue automaticamente classes
   de produção de classes de teste. Seguindo a prática padrão da literatura
   empírica, analisamos todo o código Java do repositório. Isso infla os
   valores absolutos de LOC e LCOM, mas de forma relativamente uniforme
   entre os repositórios, o que não compromete as análises de correlação.

3. **Definição de Size via `loc_total` sem contar comentários.** O PDF do
   laboratório cita "linhas de código (LOC) e linhas de comentários" como
   métrica de tamanho. CK não gera, no seu `class.csv`, uma contagem de
   linhas de comentários diretamente — os comentários estão distribuídos
   entre colunas relacionadas a Javadoc/documentação de métodos. Optamos
   por utilizar `loc_total` (soma da coluna `loc` de todas as classes) como
   proxy de Size. Para correlação esse proxy é adequado, porque LOC e
   comentários crescem juntos em projetos maiores.

### 2.6. Análise estatística

- **Teste de correlação:** **Spearman's ρ**, não Pearson. As distribuições
  de estrelas, releases e LOC total seguem cauda pesada (power-law) e
  Spearman só assume monotonicidade, não linearidade. Spearman também é
  robusto a outliers, o que é essencial para a natureza destes dados.
- **Nível de significância:** α = 0.05. Resultados com p < 0.05 são
  marcados como estatisticamente significativos nas tabelas e nos gráficos.
- **Visualização:** scatter plots em escala log (exceto idade, que é
  aproximadamente uniforme) para acomodar a dispersão das distribuições.

---

## 3. Resultados

### 3.1. Estatísticas descritivas gerais

Tabela com mediana, média, desvio padrão, mínimo e máximo de cada métrica
sobre os 1.000 repositórios analisados.

> **TODO:** inserir conteúdo de `output/analysis/descriptive_stats.csv` como
> tabela Markdown depois de rodar `python analysis.py`.

### 3.2. RQ01 — Popularidade × Qualidade

![RQ01](output/analysis/RQ01_popularity.png)

| Métrica de qualidade | Spearman ρ | p-value | Significância (α=0.05) |
|---|---|---|---|
| CBO (mediana)  | _TODO_ | _TODO_ | _TODO_ |
| DIT (mediana)  | _TODO_ | _TODO_ | _TODO_ |
| LCOM (mediana) | _TODO_ | _TODO_ | _TODO_ |

> **Análise:** _TODO — 2-3 frases interpretando os valores de ρ e p._

### 3.3. RQ02 — Maturidade × Qualidade

![RQ02](output/analysis/RQ02_maturity.png)

| Métrica de qualidade | Spearman ρ | p-value | Significância |
|---|---|---|---|
| CBO (mediana)  | _TODO_ | _TODO_ | _TODO_ |
| DIT (mediana)  | _TODO_ | _TODO_ | _TODO_ |
| LCOM (mediana) | _TODO_ | _TODO_ | _TODO_ |

> **Análise:** _TODO._

### 3.4. RQ03 — Atividade × Qualidade

![RQ03](output/analysis/RQ03_activity.png)

| Métrica de qualidade | Spearman ρ | p-value | Significância |
|---|---|---|---|
| CBO (mediana)  | _TODO_ | _TODO_ | _TODO_ |
| DIT (mediana)  | _TODO_ | _TODO_ | _TODO_ |
| LCOM (mediana) | _TODO_ | _TODO_ | _TODO_ |

> **Análise:** _TODO._

### 3.5. RQ04 — Tamanho × Qualidade

![RQ04](output/analysis/RQ04_size.png)

| Métrica de qualidade | Spearman ρ | p-value | Significância |
|---|---|---|---|
| CBO (mediana)  | _TODO_ | _TODO_ | _TODO_ |
| DIT (mediana)  | _TODO_ | _TODO_ | _TODO_ |
| LCOM (mediana) | _TODO_ | _TODO_ | _TODO_ |

> **Análise:** _TODO._

---

## 4. Discussão

### 4.1. Confronto hipóteses × resultados

| Hipótese | Esperado | Obtido | Confirmada? |
|---|---|---|---|
| H-RQ01 | Correlação negativa fraca (stars → CBO/LCOM) | _TODO_ | _TODO_ |
| H-RQ02 | Correlação positiva fraca-moderada (age → CBO/LCOM/DIT) | _TODO_ | _TODO_ |
| H-RQ03 | Correlação negativa fraca (releases → CBO/LCOM) | _TODO_ | _TODO_ |
| H-RQ04 | Correlação positiva moderada (LOC → CBO/LCOM) | _TODO_ | _TODO_ |

### 4.2. Interpretação geral

> **TODO — a escrever depois dos dados reais:**
>
> - Quais hipóteses foram **confirmadas** e por quê.
> - Quais foram **refutadas** e o que isso diz sobre as intuições iniciais.
> - Padrões inesperados nos dados (outliers, clusters, comportamento
>   não-monotônico).
> - Comparação com resultados de estudos empíricos similares em métricas CK.

---

## 5. Limitações

- **Classes de teste incluídas** na análise inflam os valores absolutos de
  LOC e LCOM; embora isso não impacte correlações significativamente,
  impacta o valor absoluto de cada métrica.
- **Definição de Size** sem contar comentários (CK não fornece esse dado
  diretamente em `class.csv`).
- **Amostra limitada aos top-1.000 por estrelas:** há viés de seleção
  — repositórios populares tendem a ser maiores, mais antigos e mais
  maduros em média do que a população total do GitHub.
- **CK conta inner classes e classes anônimas** como classes separadas,
  o que reduz o valor médio de LOC por classe mas não afeta `loc_total`.
- **Correlação não implica causalidade.** Mesmo que observemos correlações
  significativas, não podemos afirmar que uma característica de processo
  *cause* mudança na qualidade — apenas que estão associadas.

---

## 6. Como reproduzir

```bash
# 1. Dependências
pip install -r requirements.txt

# 2. Token GitHub (com scope public_repo)
cp .env.example .env
# edite .env e defina GITHUB_TOKEN

# 3. Baixar CK (do Maven Central)
curl -L -o ck.jar \
  https://repo1.maven.org/maven2/com/github/mauricioaniche/ck/0.7.0/ck-0.7.0-jar-with-dependencies.jar

# 4. Java 21+ precisa estar instalado e no PATH
java -version

# 5. Rodar o pipeline (paralelo, com resume automático)
python main.py --workers 4

# 6. Gerar tabelas e gráficos do relatório
python analysis.py
```

Todos os artefatos do relatório são escritos em `output/analysis/`:
`descriptive_stats.csv`, `spearman_correlations.csv` e os 4 PNGs por RQ.
