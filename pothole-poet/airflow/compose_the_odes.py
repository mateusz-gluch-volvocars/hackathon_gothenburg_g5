"""compose_the_odes: the Pothole Poet's hourly composition cycle.

Three tasks, two patterns:

  1. federate_pothole_reports (Operator): pull raw events from AlloyDB into
     a BigQuery staging table via Lakehouse federation.
  2. verify_federation (@task): fail fast if the staging table is empty
     (AlloyDB not seeded yet). Returns the row count via XCOM.
  3. ask_the_laureate (Operator): aggregate per neighbourhood and ask
     Gemini 3 Flash (via BigQuery AI.GENERATE) to compose a three-line ode.

The hybrid approach is intentional: Operators for service-native work (submit
SQL to BigQuery, let BigQuery do the heavy lifting), @task for Python-native
work (validation, lightweight queries, metadata). Real-world DAGs mix both.

Runs hourly. Tag a manual run from the DAGs UI to test.
"""

import datetime
import os
from pathlib import Path

from airflow import models
from airflow.decorators import task
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from airflow.sdk import Asset

# ---------------------------------------------------------------------------
# Paths & assets
# ---------------------------------------------------------------------------

# In Composer Gen 3, this DAG is uploaded to /home/airflow/gcs/dags/, and the
# sql/ folder uploaded alongside it ends up at /home/airflow/gcs/dags/sql/.
SQL_DIR = Path(__file__).parent / "sql"

neighbourhood_odes = Asset(
    "bigquery://{project}/pothole_laureate/neighbourhood_odes".format(
        project=os.environ.get("GCP_PROJECT")
        or os.environ.get("GOOGLE_CLOUD_PROJECT")
        or "unknown"
    )
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_sql(name: str) -> str:
    """Read a SQL file from the sql/ folder shipped beside this DAG."""
    text = (SQL_DIR / name).read_text(encoding="utf-8")
    project_id = (
        os.environ.get("GCP_PROJECT")
        or os.environ.get("GOOGLE_CLOUD_PROJECT")
        or os.environ.get("CLOUD_ML_PROJECT_ID")
    )
    if not project_id:
        raise RuntimeError(
            "Composer should expose the project ID via GCP_PROJECT or "
            "GOOGLE_CLOUD_PROJECT env vars; neither was set."
        )
    return text.replace("${PROJECT_ID}", project_id)


# ---------------------------------------------------------------------------
# Validation task (TaskFlow API)
# ---------------------------------------------------------------------------


@task(retries=0)
def verify_federation() -> dict:
    """Fail fast if the staging table is empty."""
    from google.cloud import bigquery

    client = bigquery.Client()
    row = next(iter(
        client.query(
            "SELECT COUNT(*) AS n FROM `pothole_laureate.pothole_reports_raw`"
        ).result()
    ))
    if row.n == 0:
        raise ValueError(
            "Federation pulled 0 rows. The AlloyDB Lead must finish Q2A-3 "
            "(Seed) before you re-trigger this DAG."
        )
    return {"federated_rows": row.n}


# ---------------------------------------------------------------------------
# DAG
# ---------------------------------------------------------------------------

with models.DAG(
    dag_id="compose_the_odes",
    doc_md=__doc__,
    description=(
        "Federate pothole reports from AlloyDB into BigQuery and ask Gemini "
        "to compose a three-line poem for each Gothenburg neighbourhood."
    ),
    start_date=datetime.datetime(2026, 5, 1),
    schedule="@hourly",
    catchup=False,
    max_active_runs=1,
    tags=["pothole-poet", "quest-1"],
    default_args={
        "owner": "the-laureate-bureau",
    },
) as dag:

    federate_pothole_reports = BigQueryInsertJobOperator(
        task_id="federate_pothole_reports",
        configuration={
            "query": {
                "query": _read_sql("01_federate.sql"),
                "useLegacySql": False,
            }
        },
        retries=2,
        retry_delay=datetime.timedelta(minutes=1),
    )

    ask_the_laureate = BigQueryInsertJobOperator(
        task_id="ask_the_laureate",
        configuration={
            "query": {
                "query": _read_sql("02_enrich.sql"),
                "useLegacySql": False,
            }
        },
        outlets=[neighbourhood_odes],
        retries=1,
        retry_delay=datetime.timedelta(minutes=2),
    )

    federate_pothole_reports >> verify_federation() >> ask_the_laureate
