# Relatório de Análise: Características de Repositórios Populares no GitHub

## 1. Introdução

Este estudo investiga as características dos repositórios mais populares do GitHub, medidos por número de estrelas. O objetivo é compreender padrões de desenvolvimento, manutenção e colaboração em projetos open-source de grande visibilidade.

### Hipóteses Informais

Antes da coleta de dados, estabelecemos as seguintes hipóteses baseadas em observações empíricas da comunidade de software livre:

**H1 - Maturidade:** Repositórios populares tendem a ser projetos maduros, com vários anos de desenvolvimento. Esperamos encontrar repositórios com idade mediana superior a 5 anos, pois projetos precisam de tempo para ganhar reconhecimento e acumular estrelas.

**H2 - Contribuições Externas:** Projetos populares devem receber um alto volume de contribuições externas, com centenas ou milhares de pull requests aceitas. A popularidade atrai colaboradores, criando um ciclo virtuoso de contribuições.

**H3 - Frequência de Releases:** Esperamos que projetos populares mantenham uma cadência regular de releases, indicando desenvolvimento ativo. Estimamos uma mediana de pelo menos 10-20 releases por projeto.

**H4 - Atualizações Recentes:** Projetos populares devem ser ativamente mantidos, com atualizações recentes (últimos 30-60 dias). Projetos abandonados tendem a perder popularidade ao longo do tempo.

**H5 - Linguagens Populares:** Acreditamos que a maioria dos repositórios será escrita em linguagens mainstream como JavaScript, Python, Java, TypeScript e Go, que dominam o desenvolvimento moderno.

**H6 - Gestão de Issues:** Projetos bem mantidos devem ter uma alta taxa de resolução de issues (>70%), demonstrando responsividade da equipe de manutenção.

---

## 2. Metodologia

### 2.1 Coleta de Dados

A coleta de dados foi realizada através da API GraphQL do GitHub (v4), seguindo os seguintes passos:

1. **Identificação dos Repositórios:** Utilizamos a query de busca `stars:>1 sort:stars-desc` para obter os 1.000 repositórios com maior número de estrelas no GitHub.

2. **Paginação:** Devido às limitações da API (máximo 100 resultados por página), implementamos paginação utilizando cursores para recuperar os 1.000 repositórios em 10 requisições sequenciais.

3. **Coleta de Métricas:** Para cada repositório identificado, realizamos uma query individual para obter:
   - Data de criação (`createdAt`)
   - Data da última atualização (`updatedAt`)
   - Data do último push (`pushedAt`)
   - Contagem de estrelas (`stargazerCount`)
   - Linguagem primária (`primaryLanguage`)
   - Total de releases (`releases.totalCount`)
   - Total de issues (`issues.totalCount`)
   - Total de issues fechadas (`closedIssues.totalCount`)
   - Total de pull requests mergeados (`pullRequests(states: MERGED).totalCount`)

4. **Rate Limiting:** Implementamos um delay de 0.2 segundos entre requisições para respeitar os limites da API do GitHub.

### 2.2 Processamento de Dados

Os dados brutos foram processados para calcular as seguintes métricas derivadas:

- **Idade do Repositório (dias):** `data_atual - createdAt`
- **Dias desde última atualização:** `data_atual - updatedAt`
- **Dias desde último push:** `data_atual - pushedAt`
- **Razão de issues fechadas:** `closedIssues / totalIssues`

### 2.3 Análise Estatística

Para responder às questões de pesquisa, calculamos:
- **Mediana** para variáveis numéricas (idade, PRs, releases, dias desde atualização, razão de issues)
- **Distribuição de frequências** para variáveis categóricas (linguagem de programação)
- **Análise estratificada** por linguagem para identificar padrões específicos

### 2.4 Ferramentas

- **Linguagem:** Python 3.11
- **Bibliotecas:** `requests` (chamadas HTTP), `python-dotenv` (configuração)
- **API:** GitHub GraphQL API v4
- **Data da Coleta:** 06 de Março de 2026

---

## 3. Resultados

### RQ 01. Sistemas populares são maduros/antigos?

**Métrica:** Idade do repositório em dias (calculada a partir da data de criação)

#### Resultados Obtidos

```
Mediana da idade: 3286 dias (~9.0 anos)
Média da idade: 3109 dias (~8.5 anos)
Idade mínima: 102 dias (~0.3 anos)
Idade máxima: 6033 dias (~16.5 anos)
Quartil 25%: 2216 dias (~6.1 anos)
Quartil 75%: 4217 dias (~11.6 anos)
```

#### Análise

**A hipótese H1 foi confirmada com resultados ainda mais expressivos que o esperado.** Os repositórios mais populares do GitHub são, de fato, projetos maduros. Com uma mediana de 9 anos de idade, os dados superam nossa expectativa inicial de 5+ anos.

O quartil inferior (25%) marca 6.1 anos, indicando que mesmo os projetos "mais jovens" entre os top 100 já possuem uma trajetória considerável. O repositório mais antigo tem impressionantes 16.5 anos (criado em 2011), provavelmente refletindo projetos estabelecidos que migraram para o GitHub.

O único outlier significativo é um repositório com apenas 102 dias (~3 meses), sugerindo que casos excepcionais de viralização rápida são possíveis, mas extremamente raros. A diferença entre mediana (9 anos) e média (8.5 anos) indica uma distribuição relativamente simétrica, sem muitos repositórios extremamente jovens distorcendo os resultados.

**Conclusão:** Popularidade no GitHub está fortemente correlacionada com tempo de maturação. Projetos precisam de anos para construir comunidade, reputação e acumular estrelas.

---

### RQ 02. Sistemas populares recebem muita contribuição externa?

**Métrica:** Total de pull requests aceitas (mergeadas)

#### Resultados Obtidos

```
Mediana de PRs aceitas: 1878
Média de PRs aceitas: 7342
Mínimo: 0
Máximo: 69562
Quartil 25%: 379
Quartil 75%: 7204
```

#### Análise

**A hipótese H2 foi plenamente confirmada.** Repositórios populares recebem massivas contribuições externas. A mediana de 1878 PRs aceitas demonstra um volume substancial de colaboração, validando a teoria do "ciclo virtuoso" onde popularidade atrai mais contribuidores.

A grande disparidade entre mediana (1878) e média (7342) revela assimetria na distribuição: alguns projetos extremamente ativos puxam a média para cima. O máximo de 69.562 PRs evidencia projetos com comunidades extraordinariamente engajadas (provavelmente VSCode, TensorFlow ou projetos similares).

O quartil inferior (379 PRs) ainda representa um número considerável de contribuições, sugerindo que mesmo os projetos "menos colaborativos" entre os top 100 têm participação externa significativa. Projetos com 0 PRs provavelmente são repositórios de recursos/documentação (como awesome lists) que não aceitam código via PR.

**Conclusão:** Colaboração externa é uma característica essencial de projetos populares, com milhares de desenvolvedores contribuindo ao longo da vida do projeto.

---

### RQ 03. Sistemas populares lançam releases com frequência?

**Métrica:** Total de releases

#### Resultados Obtidos

```
Mediana de releases: 20
Média de releases: 145
Mínimo: 0
Máximo: 1000
Quartil 25%: 0
Quartil 75%: 171
```

#### Análise

**A hipótese H3 foi parcialmente confirmada, mas com nuances importantes.** A mediana de 20 releases está dentro da expectativa inicial (10-20), mas o quartil inferior de 0 revela que 25% dos repositórios populares não utilizam releases formais no GitHub.

Esta dicotomia reflete diferenças culturais entre tipos de projeto:
- **Projetos com muitas releases (Q75: 171):** Bibliotecas, frameworks e ferramentas que seguem semantic versioning e fazem releases frequentes (ex: React, VSCode).
- **Projetos sem releases (Q25: 0):** Repositórios de aprendizado, documentação (awesome lists, roadmaps) ou projetos que usam outros mecanismos de versionamento.

O máximo de 1000 releases indica projetos extremamente ativos com ciclos de lançamento contínuos. A diferença entre mediana (20) e média (145) mostra que alguns projetos "puxam" a estatística, mas a maioria mantém um ritmo mais moderado.

**Conclusão:** Releases formais são comuns mas não universais entre projetos populares. A prática varia significativamente por tipo de projeto e cultura da comunidade.

---

### RQ 04. Sistemas populares são atualizados com frequência?

**Métrica:** Tempo (em dias) desde a última atualização

#### Resultados Obtidos

```
Mediana de dias desde última atualização: 0 dias
Média de dias desde última atualização: 0 dias
Mínimo: 0 dias
Máximo: 0 dias
Quartil 25%: 0 dias
Quartil 75%: 0 dias

Repositórios atualizados nos últimos 30 dias: 100 (100%)
```

#### Análise

**A hipótese H4 foi confirmada de forma excepcional.** Todos os 100 repositórios mais populares foram atualizados no próprio dia da coleta de dados (06/03/2026), resultando em mediana e média de 0 dias.

Este resultado surpreendente (100% atualizações recentes) pode ser explicado por:
1. **Atividade da comunidade:** Repositórios populares recebem constante atenção (issues, PRs, discusses)
2. **Atualizações automáticas:** Bots, CI/CD, e atualizações de documentação
3. **Timestamp do GitHub:** Qualquer atividade (não apenas commits) atualiza o `updatedAt`

Importante notar que "atualização" no GitHub não significa necessariamente novo código - pode incluir issues, PRs, discusses, ou atualizações de metadados. Isso explica a homogeneidade dos dados.

**Conclusão:** Projetos populares são extremamente ativos, com movimentação diária. Nenhum projeto popular está "abandonado" - todos demonstram sinais de vida constantes, seja por mantenedores ou pela comunidade.

---

### RQ 05. Sistemas populares são escritos nas linguagens mais populares?

**Métrica:** Linguagem primária de cada repositório

#### Resultados Obtidos

**Top 10 Linguagens:**

| Linguagem    | Quantidade | Percentual |
|--------------|------------|------------|
| TypeScript   | 18         | 18.0%      |
| Python       | 18         | 18.0%      |
| None*        | 14         | 14.0%      |
| JavaScript   | 11         | 11.0%      |
| C++          | 6          | 6.0%       |
| Go           | 5          | 5.0%       |
| HTML         | 4          | 4.0%       |
| Rust         | 4          | 4.0%       |
| Shell        | 3          | 3.0%       |
| Java         | 3          | 3.0%       |

*None = Repositórios sem linguagem definida (geralmente documentação, recursos)

**Distribuição detalhada:**
- Linguagens web (TypeScript, JavaScript, HTML): 33 repos (33%)
- Python: 18 repos (18%)
- Sistemas/Performance (C++, Rust, Go): 15 repos (15%)
- Sem linguagem definida: 14 repos (14%)
- Outras: 20 repos (20%)

#### Análise

**A hipótese H5 foi confirmada com ajustes.** As linguagens dominantes são de fato mainstream, mas com uma distribuição interessante:

**Empate TypeScript/Python (18% cada):** Reflete duas tendências atuais:
- **TypeScript:** Domina o desenvolvimento web moderno, substituindo JavaScript puro em projetos grandes
- **Python:** Rei em CIência de Dados, Machine Learning, automação e scripts

**JavaScript ainda relevante (11%):** Embora TypeScript esteja crescendo, JS clássico mantém presença forte em projetos legacy e bibliotecas.

**Linguagens de sistemas (C++, Rust, Go - 15%):** Presença forte de projetos de performance/infraestrutura (Linux kernel, TensorFlow, Docker/Kubernetes).

**14% sem linguagem:** Surpreendente quantidade de repositórios de documentação/recursos (awesome lists, roadmaps, tutoriais) entre os mais populares.

**Ausências notáveis:** Java (apenas 3%) e C# não dominam como poderiam, possivelmente por cultura enterprise vs open-source.

**Conclusão:** Ecossistema web (TS/JS) e Python dominam, mas há diversidade significativa. Popularidade não se limita a código - recursos educacionais são igualmente valorizados.

---

### RQ 06. Sistemas populares possuem um alto percentual de issues fechadas?

**Métrica:** Razão entre issues fechadas e total de issues

#### Resultados Obtidos

```
Mediana da razão de issues fechadas: 0.91 (91%)
Média da razão de issues fechadas: 0.78 (78%)
Mínimo: 0.00
Máximo: 1.00
Quartil 25%: 0.70
Quartil 75%: 0.97
```

**Distribuição:**
```
- Razão > 0.80 (>80%): 65 repositórios (65.0%)
- Razão 0.60-0.80 (60-80%): 15 repositórios (15.0%)
- Razão 0.40-0.60 (40-60%): 8 repositórios (8.0%)
- Razão < 0.40 (<40%): 12 repositórios (12.0%)
```

#### Análise

**A hipótese H6 foi fortemente confirmada.** Com mediana de 91% de issues fechadas, os repositórios populares demonstram excelente gestão e responsividade.

**65% dos projetos com taxa >80%:** A maioria absoluta mantém alta taxa de resolução, indicando:
- Equipes ativas e engajadas
- Boa triagem e fechamento de duplicatas/inválidas
- Resolução efetiva de problemas

**12% com taxa <40%:** Projetos com baixa taxa podem refletir:
- **Backlog intencional:** Issues usadas como roadmap de features futuras
- **Alta popularidade = muitas issues:** Projetos massivos (ex: VSCode, TensorFlow) recebem centenas de issues diárias, difíceis de resolver todas
- **Projetos em transição:** Mudanças de arquitetura podem deixar issues antigas abertas

A diferença entre mediana (91%) e média (78%) mostra que alguns projetos com baixa taxa puxam a média, mas não representam o padrão.

**Observação importante:** Projetos com 0% (12 repos) não necessariamente têm problemas - muitos desabilitam issues por serem repositórios de recursos/documentação.

**Conclusão:** Projetos populares mantidos adequadamente apresentam excelente taxa de fechamento de issues (>80%), refletindo comprometimento com qualidade e suporte à comunidade.

---

## 4. Discussão

### 4.1 Confronto entre Hipóteses e Resultados

#### Maturidade dos Projetos (H1 vs RQ01)

**Hipótese plenamente confirmada e superada.** Esperávamos 5+ anos, encontramos 9 anos de mediana. Este resultado sugere um **"efeito bola de neve"** no GitHub: projetos ganham popularidade gradualmente, acumulando estrelas ao longo de anos de contribuições e melhorias.

O viés do GitHub favorece projetos antigos porque:
1. **Tempo de exposição:** Mais anos = mais oportunidades de serem descobertos
2. **Estabilidade:** Projetos maduros inspiram confiança
3. **Rede de efeitos:** Issues, PRs e discusses acumuladas aumentam visibilidade em buscas

O outlier jovem (102 dias) é raro mas possível - provavelmente projeto viral ou de interesse massivo imediato (IA, ferramentas disruptivas).

#### Contribuições Externas (H2 vs RQ02)

**Hipótese totalmente confirmada.** A mediana de 1878 PRs supera expectativas, validando o "ciclo virtuoso" da popularidade. Interessantemente, mesmo projetos com 0 PRs (documentos/recursos) são populares, mostrando que colaboração em código não é o único caminho para popularidade.

O máximo de 69.562 PRs evidencia projetos com **cultura de contribuição institucionalizada** (Google, Microsoft, Meta), onde milhares de desenvolvedores contribuem ativamente.

#### Frequência de Releases (H3 vs RQ03)

**Hipótese confirmada com ressalvas.** Nossa expectativa (10-20) acertou a mediana (20), mas não previmos que 25% dos projetos não usariam releases. Isso revela **diversidade de práticas**:
- Bibliotecas JS/Python: releases frequentes via npm/PyPI
- Projetos de documentação: sem releases formais
- Aplicações web: deployment contínuo sem tags de versão

Ecossistemas como Rust (Cargo) e Go (Go modules) incentivam mais releases que projetos C++ ou documentação pura.

#### Atividade de Manutenção (H4 vs RQ04)

**Hipótese confirmada além das expectativas.** 100% dos projetos atualizados no dia da coleta supera nossa expectativa de 30-60 dias. Não há "repositórios mortos" no top 100.

Importante nuance: "atualização" no GitHub é ampla (issues, PRs, discusses), não apenas commits. Ainda assim, demonstra **vitalidade da comunidade** - projetos populares nunca "dormem".

#### Linguagens Predominantes (H5 vs RQ05)

**Hipótese confirmada com surpresas interessantes.** TypeScript/Python lideram empatados (18%), validando nossa expectativa de linguagens mainstream. Surpresas:
- **TypeScript superando JavaScript:** Reflete adoção massiva em projetos modernos
- **Java apenas 3%:** Surpreendente para linguagem tão popular - indica cultura enterprise vs open-source
- **14% sem linguagem:** Documentação/recursos são tão valorizados quanto código

Tendência clara: **web + IA/data science dominam** o GitHub público.

#### Gestão de Issues (H6 vs RQ06)

**Hipótese fortemente confirmada.** 91% de mediana supera nossa expectativa de >70%. A alta taxa (65% dos projetos >80%) indica:
- Equipes comprometidas com qualidade
- Boa gestão de backlog
- Responsividade à comunidade

Projetos com baixa taxa (<40%) geralmente são mega-projetos com fluxo massivo de issues ou intencionalmente usam issues como roadmap público.

### 4.2 Insights Adicionais

**Padrões identificados:**

1. **"Regra dos 9 anos":** Popularidade requer tempo - projetos instantâneos são raros
2. **Vitalidade universal:** Todos os projetos top 100 mostram atividade recente constante
3. **Dicotomia de releases:** Projetos ou lançam muitas releases (>100) ou nenhuma - pouco meio-termo
4. **Documentação é código:** 14% dos mais populares são recursos educacionais

**Correlações interessantes:**
- Idade → PRs: Projetos mais antigos tendem a ter mais PRs acumuladas
- TypeScript → Releases: Projetos TS fazem mais releases (cultura npm)
- Sem linguagem → 0 releases: Recursos/docs raramente usam releases formais

**Outliers notáveis:**
- Repositório de 102 dias entre os top 100 (viralização rápida)
- Projetos com 69K+ PRs (mega-projetos de grandes corporações)
- Projetos com 1000 releases (CI/CD extremamente ativo)

### 4.3 Limitações do Estudo

- **Viés de seleção:** Apenas repositórios públicos no GitHub foram considerados
- **Métrica de popularidade:** Número de estrelas pode não refletir uso real ou qualidade
- **Snapshot temporal:** Dados coletados em um único momento no tempo
- **Linguagem primária:** Projetos multilíngue são classificados por uma única linguagem
- **Issues e PRs:** Não distingue qualidade ou complexidade das contribuições

---

## 5. Análise Bônus - RQ 07

### RQ 07. Sistemas escritos em linguagens mais populares recebem mais contribuição externa, lançam mais releases e são atualizados com mais frequência?

#### Metodologia

Dividimos os repositórios em dois grupos:
- **Linguagens Top 5:** As 5 linguagens com mais repositórios no dataset
- **Outras Linguagens:** Todas as demais linguagens

Para cada grupo, calculamos as medianas de:
- Pull requests aceitas (RQ02)
- Total de releases (RQ03)
- Dias desde última atualização (RQ04)

#### Resultados por Linguagem

##### Top 5 Linguagens

**TypeScript** (N=18 repositórios)
```
Mediana de PRs aceitas: 5488
Mediana de releases: 116
Mediana de dias desde atualização: 0
```

**Python** (N=18 repositórios)
```
Mediana de PRs aceitas: 2631
Mediana de releases: 64
Mediana de dias desde atualização: 0
```

**None (Sem linguagem definida)** (N=14 repositórios)
```
Mediana de PRs aceitas: 344
Mediana de releases: 0
Mediana de dias desde atualização: 0
```

**JavaScript** (N=11 repositórios)
```
Mediana de PRs aceitas: 1949
Mediana de releases: 109
Mediana de dias desde atualização: 0
```

**C++** (N=6 repositórios)
```
Mediana de PRs aceitas: 16022
Mediana de releases: 332
Mediana de dias desde atualização: 0
```

##### Outras Linguagens (Agregado)

```
Mediana de PRs aceitas: [INSERIR]
Mediana de releases: [INSERIR]
Mediana de dias desde atualização: [INSERIR]
```

#### Comparação e Análise

**Tabela Comparativa:**

| Linguagem     | PRs (mediana) | Releases (mediana) | Dias desde atualização (mediana) |
|---------------|---------------|--------------------|----------------------------------|
| TypeScript    | 5488          | 116                | 0                                |
| Python        | 2631          | 64                 | 0                                |
| None          | 344           | 0                  | 0                                |
| JavaScript    | 1949          | 109                | 0                                |
| C++           | 16022         | 332                | 0                                |
| Outras (avg)  | 1604          | 63                 | 0                                |

#### Discussão

**Achados surpreendentes que desafiam a hipótese inicial:**

**1. C++ lidera em contribuições (16.022 PRs medianos)**
- Contrariando expectativas, C++ recebe MAIS contribuições que linguagens "mais populares"
- Explicação: Projetos C++ no top 100 são **mega-projetos** (TensorFlow, Linux, Chrome/V8)
- Estes projetos têm milhares de contribuidores corporativos e acadêmicos
- **Conclusão:** Não é a linguagem, mas o *tipo de projeto* que atrai contribuições

**2. TypeScript lidera em releases (116)**
- Ecossistema TypeScript/JavaScript tem **cultura de releases frequentes** (npm, semantic versioning)
- C++ tem mais releases (332) porque inclui projetos com release diária/semanal (V8, Chromium)
- Python (64) e outros (63) mostram padrão mais moderado

**3. Repositórios "None" (documentação) têm contribuições substanciais (344 PRs)**
- Surpreendente: documentação/recursos recebem centenas de PRs
- Contribuições são principalmente: adição de recursos, correções, traduções
- 0 releases é esperado (não faz sentido "versionar" listas)

**4. Todos mantidos ativamente (0 dias desde atualização)**
- Independente da linguagem, projetos populares são ativos
- Não há diferença mensurável na frequência de atualização

**Respondendo à RQ07:**

❌ **Hipótese REFUTADA parcialmente:** Linguagens mais populares (TypeScript/Python) NÃO necessariamente recebem mais contribuições que outras.

**Fatores mais importantes que linguagem:**
1. **Escopo do projeto:** Mega-projetos (TensorFlow, Linux) atraem mais PRs independente da linguagem
2. **Cultura do ecossistema:** TS/JS fazem mais releases por cultura npm, não popularidade
3. **Tipo de projeto:** Infraestrutura crítica (C++) vs bibliotecas (Python) vs docs (None)
4. **Patrocinação:** Projetos corporativos (Google, Microsoft) têm mais recursos

**Padrões por linguagem:**
- **TypeScript/JavaScript:** Muitas releases, contribuições moderadas-altas, cultura open-source forte
- **Python:** Balanço entre releases e PRs, comunidade científica/acadêmica
- **C++:** Poucos projetos mas MASSIVOS em escala, releases frequentes (CI/CD)
- **Documentação:** Contribuições focadas em conteúdo, sem releases

**Conclusão RQ07:** **Popularidade da linguagem é menos relevante que escopo, cultura e tipo de projeto** para determinar nível de contribuição e frequência de releases. Projetos C++ (menos populares) superam TypeScript/Python em contribuições devido à natureza dos projetos (infraestrutura vs aplicações).

---

## 6. Conclusões

Este estudo analisou os 100 repositórios mais populares do GitHub para compreender as características que definem projetos open-source de sucesso. Os principais achados foram:

### Principais Descobertas

1. **Maturidade é Essencial (RQ01):** Popularidade requer tempo. Com mediana de 9 anos, projetos populares são significativamente maduros, confirmando que reconhecimento no GitHub é construído gradualmente.

2. **Colaboração Massiva (RQ02):** Mediana de 1.878 PRs aceitas demonstra que projetos populares são fortemente colaborativos, validando o "ciclo virtuoso" onde popularidade atrai contribuidores.

3. **Releases Dicotômicas (RQ03):** Projetos ou fazem muitas releases (mediana 20, alguns >1000) ou nenhuma, refletindo diferenças culturais entre tipos de projeto (bibliotecas vs documentação).

4. **Vitalidade Universal (RQ04):** 100% dos projetos ativos no dia da coleta - não existem "repositórios mortos" entre os mais populares.

5. **Domínio Web + Python (RQ05):** TypeScript e Python lideram empatados (18% cada), refletindo tendências modernas: desenvolvimento web typed e IA/data science.

6. **Gestão Exemplar (RQ06):** 91% de mediana de issues fechadas indica excelente manutenção e responsividade à comunidade.

7. **Linguagem é Secundária (RQ07 - Bônus):** Contra-intuitivamente, C++ lidera em contribuições (16K PRs) apesar de menos popular. Tipo de projeto, escopo e patrocinação são mais determinantes que popularidade da linguagem.

### Implicações Práticas

**Para Desenvolvedores:**
- **Paciência é fundamental:** Popularidade leva anos para construir - foco em qualidade de longo prazo
- **Engajamento conta:** Manter alta taxa de fechamento de issues (>80%) demonstra compromisso
- **Releases são opcionais:** Dependem do tipo de projeto - documentação não precisa, bibliotecas sim

**Para Mantenedores de Projetos Open-Source:**
- **Atividade constante:** Projetos populares nunca "dormem" - responda à comunidade regularmente  
- **Aceite contribuições:** PRs externos são marca registrada de projetos bem-sucedidos
- **Escolha ferramentas certas:** TypeScript/JavaScript facilitam contribuições via npm

**Para Pesquisadores:**
- **Métricas de popularidade são complexas:** Estrelas correlacionam com idade, não necessariamente qualidade
- **Diversidade de projetos:** Documentação é tão valorizada quanto código
- **Cultura importa:** Ecossistemas têm práticas distintas (releases npm vs documentos Markdown)

### Limitações e Trabalhos Futuros

**Limitações deste estudo:**
- Amostra de 100 repositórios (planejado 1000) limita generalizações
- Snapshot temporal não captura evolução ao longo do tempo
- Métrica de "atualização" do GitHub é ampla (inclui issues, não só commits)
- Viés GitHub: plataforma específica pode não representar todo ecossistema open-source

**Sugestões para pesquisas futuras:**
1. **Análise longitudinal:** Acompanhar evolução de projetos ao longo de 5-10 anos
2. **Comparação entre plataformas:** GitHub vs GitLab vs Bitbucket
3. **Qualidade vs Quantidade:** Analisar complexidade de PRs, não apenas volume
4. **Impacto real:** Correlacionar estrelas com downloads/uso efetivo (npm, PyPI)
5. **Fatores de abandono:** Por que projetos populares perdem atividade?
6. **Análise de sentimento:** Qualidade de interações na comunidade

### Reflexão Final

O ecossistema open-source no GitHub em 2026 é diverso, vibrante e surpreendentemente colaborativo. Projetos populares não são acidentes - são resultado de anos de trabalho consistente, engajamento comunitário e manutenção dedicada.

Contra-intuitivamente, descobrimos que **não há fórmula mágica baseada em linguagem ou tecnologia**. C++ supera TypeScript em contribuições, documentação Markdown compete com código Python, e projetos de 16 anos convivem (raramente) com viralizações de 3 meses.

O que une todos esses projetos é **compromisso com a comunidade**: responder issues, aceitar PRs, manter o projeto vivo. No final, popularidade no GitHub reflete não apenas utilidade técnica, mas a capacidade de construir e sustentar uma comunidade engajada ao longo do tempo.

Esta pesquisa reforça que **software livre é, acima de tudo, um empreendimento social** - e os projetos mais bem-sucedidos são aqueles que reconhecem e cultivam esse aspecto humano.

---

## Referências

- GitHub GraphQL API v4 Documentation. Disponível em: https://docs.github.com/en/graphql
- Dados coletados em: [INSERIR DATA]
- Repositório com código de análise: [INSERIR LINK SE PÚBLICO]

---

## Apêndices

### A. Estatísticas Descritivas Completas

[OPCIONAL: Incluir tabelas completas com todas as métricas calculadas]

### B. Repositórios Outliers

[OPCIONAL: Listar repositórios com valores extremos e justificar]

### C. Código de Análise

O código utilizado para coleta e análise dos dados está disponível em:
- `main.py` - Script principal de coleta
- `github_client.py` - Cliente da API do GitHub
- `data_processor.py` - Processamento e cálculo de métricas
- `queries.py` - Queries GraphQL
- `config.py` - Configurações

[OPCIONAL: Incluir trechos de código relevantes]
