import requests
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from dotenv import load_dotenv
import os
import time

load_dotenv()


def _clean_env(value: str | None, default: str) -> str:
    if value is None:
        return default

    cleaned = value.strip()
    if cleaned == "" or cleaned.lower() == "none":
        return default

    return cleaned


# --- db connection ---
db_user = _clean_env(os.getenv("DB_USER"), "druguser")
db_password = _clean_env(os.getenv("DB_PASSWORD"), "drugpass")
db_host = _clean_env(os.getenv("DB_HOST"), "localhost")
db_name = _clean_env(os.getenv("DB_NAME"), "drugdb")
db_port_raw = _clean_env(os.getenv("DB_PORT"), "5432")

try:
    db_port = int(db_port_raw)
except ValueError as exc:
    raise ValueError(f"Invalid DB_PORT value: {db_port_raw!r}. Expected an integer.") from exc

DB_URL = URL.create(
    drivername="postgresql",
    username=db_user,
    password=db_password,
    host=db_host,
    port=db_port,
    database=db_name,
)
engine = create_engine(DB_URL)

# openFDA base url , no key needed
FDA_BASE = "https://api.fda.gov/drug/event.json"

# drugs we want to look at 
DRUGS_TO_FETCH = [
    "ibuprofen",
    "aspirin",
    "metformin",
    "lisinopril",
    "amoxicillin",
    "atorvastatin",
    "omeprazole",
]


def fetch_drug_events(drug_name: str, limit: int = 100) -> list[dict]:
    """
    pull adverse event reports from openfda for a given drug name.
    returns a list of raw report dicts.
    """
    params = {
        "search": f'patient.drug.medicinalproduct:"{drug_name}"',
        "limit": limit,
    }

    print(f"  fetching data for: {drug_name}")
    response = requests.get(FDA_BASE, params=params, timeout=15)

    # if the api returns no results for a drug, skip it quietly
    if response.status_code == 404:
        print(f"  no results found for {drug_name}, skipping")
        return []

    response.raise_for_status()
    data = response.json()

    return data.get("results", [])


def parse_events(events: list[dict], drug_name: str) -> list[dict]:
    """
    flatten the nested fda json into something we can put in a table.
    the fda response is deeply nested so we pull out just what we need.
    """
    rows = []

    for event in events:
        # some fields might be missing so we use .get() everywhere
        report_id = event.get("safetyreportid", None)
        receive_date = event.get("receivedate", None)
        serious = event.get("serious", None)  # 1=serious, 2=not serious
        country = event.get("primarysourcecountry", None)

        # patient info is nested one level deeper
        patient = event.get("patient", {})
        patient_age = patient.get("patientonsetage", None)
        patient_sex = patient.get("patientsex", None)  # 1=male, 2=female

        # reactions is a list, we join them into one string
        reactions = patient.get("reaction", [])
        reaction_names = ", ".join(
            r.get("reactionmeddrapt", "") for r in reactions if r.get("reactionmeddrapt")
        )

        rows.append({
            "report_id": report_id,
            "drug_name": drug_name,
            "receive_date": receive_date,
            "serious": serious,
            "country": country,
            "patient_age": patient_age,
            "patient_sex": patient_sex,
            "reactions": reaction_names,
        })

    return rows


def create_raw_table():
    """create the raw table if it doesnt exist yet."""
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS raw_drug_events (
                report_id       TEXT,
                drug_name       TEXT,
                receive_date    TEXT,
                serious         TEXT,
                country         TEXT,
                patient_age     TEXT,
                patient_sex     TEXT,
                reactions       TEXT,
                loaded_at       TIMESTAMP DEFAULT NOW()
            );
        """))
        conn.commit()
    print("raw table ready")


def load_to_postgres(df: pd.DataFrame):
    """append the parsed rows into our raw table."""
    df.to_sql(
        name="raw_drug_events",
        con=engine,
        if_exists="append",   # append, not replace to keep all data
        index=False,
    )


def run():
    print("starting ETL...")
    create_raw_table()

    all_rows = []

    for drug in DRUGS_TO_FETCH:
        events = fetch_drug_events(drug)

        if not events:
            continue

        rows = parse_events(events, drug)
        all_rows.extend(rows)

        # small sleep to not hammer the api
        time.sleep(0.5)

    if not all_rows:
        print("no data fetched, something might be wrong")
        return

    df = pd.DataFrame(all_rows)
    print(f"\ntotal rows fetched: {len(df)}")

    load_to_postgres(df)
    print("done - data loaded into postgres")
    print("you can now open pgadmin at http://localhost:8080 to explore the data")


if __name__ == "__main__":
    run()
