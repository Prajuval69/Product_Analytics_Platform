"""Real Apache Airflow 2.10 DAG; the isolated analytics environment avoids dbt conflicts."""

from datetime import timedelta

import pendulum

from airflow import DAG
from airflow.operators.bash import BashOperator

STAGES = [
    ("generate_data", "generate"),
    ("load_raw", "load"),
    ("validate_raw", "quality"),
    ("dbt_parse", "dbt-parse"),
    ("dbt_staging", "dbt-staging"),
    ("dbt_intermediate", "dbt-intermediate"),
    ("dbt_marts", "dbt-marts"),
    ("dbt_tests", "dbt-test"),
    ("build_ml_features", "features"),
    ("train_churn_model", "ml"),
    ("dbt_final_tests", "dbt-test"),
    ("export_bi", "export"),
    ("final_validation", "verify"),
    ("dbt_documentation", "dbt-docs"),
]

with DAG(
    dag_id="product_analytics_pipeline",
    description="Deterministic SaaS analytics: raw COPY, dbt, quality, temporal churn model, BI",
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    default_args={
        "owner": "analytics",
        "retries": 2,
        "retry_delay": timedelta(minutes=1),
        "execution_timeout": timedelta(minutes=45),
    },
    tags=["product", "dbt", "synthetic", "portfolio"],
    doc_md="Source horizon is fixed by HISTORY_START/HISTORY_END. Repeated runs replace snapshots atomically. See docs/AIRFLOW.md.",
) as dag:
    previous = None
    for task_id, command in STAGES:
        task = BashOperator(
            task_id=task_id,
            bash_command=f"cd /opt/platform && /opt/analytics-venv/bin/python -m platform_app.cli {command}",
            append_env=True,
            env={
                "PATH": "/opt/analytics-venv/bin:/home/airflow/.local/bin:/usr/local/bin:/usr/bin:/bin"
            },
        )
        if previous is not None:
            previous >> task
        previous = task
