"""Small end-to-end build and incremental rerun using synthetic source files.

Run in the Airflow image only, with DB_NAME=nyc_taxi_test and
TAXI_DATA_DIR=/tmp/taxi-smoke. This resets schemas in the dedicated test database.
Never point this command at the normal warehouse or historical local data.
"""
from datetime import date
import os
from pathlib import Path
import subprocess

import pyarrow as pa
import pyarrow.parquet as pq
import psycopg2

from ingestion.download_data import LOOKUP_PATH
from pipeline.config import DATA_DIR, PROJECT_ROOT, partition_path
from pipeline.spark_support import create_spark
from pipeline.warehouse import load_month, connection_options
from spark.bronze_to_silver import TYPES, process_month
from spark.silver_to_gold import enrich


def fixture(year, month, reduced=False):
    row = {name: "0" for name in TYPES}
    row.update(VendorID="1", tpep_pickup_datetime=f"{year}-{month:02d}-05 10:00:00",
               tpep_dropoff_datetime=f"{year}-{month:02d}-05 10:20:00", passenger_count=None,
               trip_distance="4.5", RatecodeID="1", store_and_fwd_flag="N",
               PULocationID="158", DOLocationID="233", payment_type="1",
               fare_amount="20.00", tip_amount="4.00", total_amount="29.00", cbd_congestion_fee="2.50")
    if year < 2025:
        row.pop("cbd_congestion_fee")
    other = {**row, "DOLocationID": "158", "fare_amount": "10.00", "total_amount": "19.00"}
    rows = [other] if reduced else [row, other, row, {**row, "DOLocationID": "999"}]
    path = partition_path("bronze", year, month) / f"yellow_tripdata_{year}-{month:02d}.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(rows, schema=pa.schema([(name, pa.string()) for name in row])), path)


def dbt_build(start, end):
    env = {**os.environ, "PIPELINE_START_MONTH": start, "PIPELINE_END_MONTH": end}
    subprocess.run(["dbt", "--log-path", "/tmp/dbt-smoke-logs", "build", "--project-dir", str(PROJECT_ROOT / "dbt"),
                    "--profiles-dir", str(PROJECT_ROOT / "dbt"), "--target-path", "/tmp/dbt-smoke-target"], env=env, check=True)


def main():
    if os.getenv("DB_NAME") != "nyc_taxi_test" or DATA_DIR != Path("/tmp/taxi-smoke"):
        raise RuntimeError("Smoke testing requires DB_NAME=nyc_taxi_test and TAXI_DATA_DIR=/tmp/taxi-smoke")
    with psycopg2.connect(**connection_options()) as conn:
        with conn.cursor() as cur:
            for schema in ["gold", "load_stage", "staging", "core", "mart", "reference"]:
                cur.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
    fixture(2024, 12)
    fixture(2025, 1)
    spark = create_spark("Taxi end-to-end smoke", jdbc=True)
    try:
        zones = spark.read.option("header", True).csv(str(LOOKUP_PATH))
        def publish(year, month):
            process_month(spark, year, month)
            silver = spark.read.parquet(str(partition_path("silver", year, month)))
            gold = enrich(silver, zones)
            load_month(gold, year, month, gold.count())
        publish(2024, 12)
        publish(2025, 1)
        dbt_build("2024-12", "2025-01")
        fixture(2025, 1, reduced=True)
        publish(2025, 1)
        dbt_build("2025-01", "2025-01")
    finally:
        spark.stop()
    with psycopg2.connect(**connection_options()) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT source_month, COUNT(*) FROM core.fact_trips GROUP BY 1 ORDER BY 1")
            assert cur.fetchall() == [(date(2024, 12, 1), 2), (date(2025, 1, 1), 1)]
            cur.execute("SELECT COUNT(*) FROM core.dim_time")
            assert cur.fetchone()[0] == 24
            cur.execute("SELECT month_start, SUM(total_revenue) FROM mart.mart_kpi_summary GROUP BY 1 ORDER BY 1")
            assert cur.fetchall() == [(date(2024, 12, 1), 48), (date(2025, 1, 1), 19)]
            cur.execute("GRANT USAGE ON SCHEMA mart TO bi_reader")
            cur.execute("GRANT SELECT ON ALL TABLES IN SCHEMA mart TO bi_reader")
    print("PASS: source schema evolution, quality, JDBC, dbt tests and selected-month replacement; December preserved.")


if __name__ == "__main__":
    main()
