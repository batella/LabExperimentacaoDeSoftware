# Lab 02 – Java Quality Study

Automated pipeline to collect the **top-1 000 Java repositories** from GitHub
and analyse their internal quality using the [CK](https://github.com/mauricioaniche/ck) static-analysis tool.

## Research Questions

| ID  | Question |
|-----|----------|
| RQ01 | Relation between **popularity** (stars) and quality metrics |
| RQ02 | Relation between **maturity** (age in years) and quality metrics |
| RQ03 | Relation between **activity** (releases) and quality metrics |
| RQ04 | Relation between **size** (LOC via CK) and quality metrics |

Quality metrics measured: **CBO**, **DIT**, **LCOM** (class-level, summarised per repo).

---

## Project Structure

```
laboratorio_2/
├── config.py          # All constants and environment variable handling
├── queries.py         # GraphQL query templates
├── github_client.py   # GitHub GraphQL API client
├── repo_processor.py  # Normalise raw API nodes → flat dicts
├── ck_runner.py       # Clone repos and run the CK JAR
├── ck_parser.py       # Parse CK CSV output and compute statistics
├── exporter.py        # Write results to CSV
├── main.py            # CLI entry point – orchestrates the pipeline
├── requirements.txt
├── .env.example
└── output/
    ├── repositories_list.csv   ← list of 1 000 repos
    ├── metrics_summary.csv     ← combined process + quality data
    └── ck_results/             ← per-repo CK output directories
```

---

## Setup

### Option A – Docker (recommended)

```bash
cp .env.example .env
# Add your GITHUB_TOKEN to .env

# Download CK JAR
wget https://github.com/mauricioaniche/ck/releases/download/0.7.1/ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar \
     -O ck.jar

# Sprint 1 demo (CK on first repo only)
docker compose up --build

# Full run (all 1 000 repos)
docker compose run --rm lab02 --limit 1000
```

Output files land in `./output/` on the host.

### Option B – Local Python environment

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Add your GITHUB_TOKEN to .env

wget https://github.com/mauricioaniche/ck/releases/download/0.7.1/ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar \
     -O ck.jar
```

---

## Running (local)

### Sprint 1 – Demo (1 repository, full CSV output)

```bash
python main.py --ck-only-first
```

### Full run (all 1 000 repositories)

```bash
python main.py
```

### Options

| Flag | Description |
|------|-------------|
| `--limit N` | Process only the first N repositories |
| `--keep-clones` | Keep local clones after CK runs |
| `--ck-only-first` | Run CK only on the first repository |

---

## Output

| File | Contents |
|------|----------|
| `output/repositories_list.csv` | owner, name, URL, stars, releases, age |
| `output/metrics_summary.csv` | all above + CBO/DIT/LCOM mean, median, stdev per repo |

---

## Requirements

- Python 3.10+
- git (in PATH)
- Java 11+ (for the CK JAR)
