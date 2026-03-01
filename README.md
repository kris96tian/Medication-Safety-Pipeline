# Medication Safety Pipeline

A pipeline that turns raw FDA medication reports into a searchable database of side effects and patient outcomes, using real data from the [OpenFDA public API](https://open.fda.gov/apis/drug/event/).

---

## What it does

The FDA collects reports from patients and healthcare providers about negative reactions to drugs. This project pulls those reports for a set of common medications, stores them raw, then builds two analytics models on top:

- which drugs have the highest rate of serious adverse events
- which reactions show up most often per drug, and how serious they tend to be

---

## Architecture

```
OpenFDA API
    |
    v
extract_load.py        # pulls JSON, flattens it, loads into postgres
    |
    v
raw_drug_events        # raw table in postgres (public schema)
    |
    v
stg_drug_events        # dbt staging: clean types, decode FDA codes
    |
    v
mart_drug_summary      # aggregated metrics per drug
mart_reaction_frequency  # reaction counts per drug
```

---

## Project structure

```
medication-safety-pipeline/
├── docker-compose.yml          # postgres + pgadmin
├── requirements.txt
├── etl/
│   └── extract_load.py         # extract from FDA, load into postgres
└── dbt_project/
    ├── dbt_project.yml
    ├── profiles/
    │   └── profiles.yml        # dbt connection config
    └── models/
        ├── staging/
        │   └── stg_drug_events.sql
        └── marts/
            ├── mart_drug_summary.sql
            └── mart_reaction_frequency.sql
```

---

## Stack

| Tool | Purpose |
|---|---|
| Python | ETL script |
| requests + pandas | API calls and data wrangling |
| PostgreSQL | data storage |
| dbt | data transformation and modeling |
| Docker + Docker Compose | local Postgres and pgAdmin |

---

## Quickstart

```bash
# install dependencies
pip install -r requirements.txt
pip install dbt-postgres

# start postgres and pgadmin
docker compose up -d

# run the ETL
python etl/extract_load.py

# run dbt models
cd dbt_project
export DBT_PROFILES_DIR=./profiles
dbt run
```

pgAdmin is available at `http://localhost:8080`
- Email: `admin@admin.com`
- Password: `admin`
- DB host (when adding server): `postgres`, port `5432`, user `druguser`, password `drugpass`

---

## Example queries

```sql
-- drugs with the highest share of serious reports
select drug_name, total_reports, pct_serious
from analytics.mart_drug_summary
order by pct_serious desc;

-- most common reactions for ibuprofen
select reaction, report_count
from analytics.mart_reaction_frequency
where drug_name = 'ibuprofen'
order by report_count desc
limit 10;
```

---

## Results

See [analysis_results.md](analysis_results.md) for query results and findings.

---

## Data source

OpenFDA Drug Adverse Event API - https://open.fda.gov/apis/drug/event/

