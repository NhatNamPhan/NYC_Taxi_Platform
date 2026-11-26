"""Manually select months; serialize writers and pass parameters as environment."""
from datetime import timedelta
import os
import pendulum
from airflow import DAG
from airflow.models.param import Param
from airflow.operators.bash import BashOperator

ROOT = "/opt/airflow"
MONTH_PATTERN = r"^20[0-9]{2}-(0[1-9]|1[0-2])$"

with DAG(
    "nyc_taxi_pipeline",
    description="Monthly NYC taxi ingestion, quality checks, warehouse and dbt marts",
    start_date=pendulum.datetime(2024, 1, 1, tz="America/New_York"),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    max_active_tasks=1,
    default_args={"owner": "data-platform", "retries": 1, "retry_delay": timedelta(minutes=3),
                  "execution_timeout": timedelta(hours=6)},
    params={
        "start_month": Param(os.getenv("PIPELINE_START_MONTH", "2025-01"), type="string", pattern=MONTH_PATTERN),
        "end_month": Param(os.getenv("PIPELINE_END_MONTH", "2025-01"), type="string", pattern=MONTH_PATTERN),
    },
    tags=["nyc-taxi", "monthly", "quality"],
) as dag:
    selected_months = {
        "PIPELINE_START_MONTH": "{{ params.start_month }}",
        "PIPELINE_END_MONTH": "{{ params.end_month }}",
    }

    def task(task_id, command):
        return BashOperator(task_id=task_id, bash_command=command, cwd=ROOT,
                            env=selected_months, append_env=True)

    download = task("download_data_bronze", "python -m ingestion.download_data")
    silver = task("spark_bronze_to_silver", "python -m spark.bronze_to_silver")
    gold = task("spark_silver_to_gold", "python -m spark.silver_to_gold")
    dbt_build = task("dbt_transform_marts", "dbt build --project-dir /opt/airflow/dbt --profiles-dir /opt/airflow/dbt")
    download >> silver >> gold >> dbt_build
