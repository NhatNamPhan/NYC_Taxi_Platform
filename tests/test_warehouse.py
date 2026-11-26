"""Real JDBC and transaction regression, isolated in the dedicated test database."""
import os
import pytest
import psycopg2
from pipeline.warehouse import load_month, connection_options
from spark.bronze_to_silver import normalize, classify
from pyspark.sql import functions as F

pytestmark = [pytest.mark.warehouse, pytest.mark.skipif(os.getenv("RUN_WAREHOUSE_TESTS") != "1", reason="Dedicated warehouse integration is opt-in")]


def test_month_replacement_removes_stale_rows_and_rollback_preserves_previous_load(raw_frame, source_row, monkeypatch):
    monkeypatch.setenv("DB_NAME", "nyc_taxi_test")
    with psycopg2.connect(**connection_options()) as conn:
        with conn.cursor() as cur:
            cur.execute("DROP SCHEMA IF EXISTS gold CASCADE")
    jan = classify(normalize(raw_frame([source_row]), 2025, 1), 2025, 1).drop("rejection_reasons")
    feb_row = {**source_row, "tpep_pickup_datetime": "2025-02-01 00:09:08", "tpep_dropoff_datetime": "2025-02-01 00:31:26"}
    feb = classify(normalize(raw_frame([feb_row]), 2025, 2), 2025, 2).drop("rejection_reasons")
    load_month(jan, 2025, 1, 1)
    load_month(feb, 2025, 2, 1)
    changed = jan.withColumn("fare_amount", F.lit(99).cast("decimal(18,2)"))
    load_month(changed, 2025, 1, 1)
    options = connection_options()
    with psycopg2.connect(**options) as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT source_month, "fare_amount" FROM gold.trips ORDER BY source_month')
            rows = cur.fetchall()
            assert len(rows) == 2 and rows[0][1] == 99 and rows[1][1] != 99
    with pytest.raises(ValueError, match="Staging validation"):
        load_month(jan, 2025, 1, 999)
    with psycopg2.connect(**options) as conn:
        with conn.cursor() as cur:
            cur.execute("""CREATE OR REPLACE FUNCTION gold.reject_test_insert() RETURNS TRIGGER LANGUAGE plpgsql AS $$
                BEGIN RAISE EXCEPTION 'simulated publish failure'; END $$""")
            cur.execute("CREATE TRIGGER test_reject BEFORE INSERT ON gold.trips FOR EACH ROW EXECUTE FUNCTION gold.reject_test_insert()")
    try:
        with pytest.raises(psycopg2.Error, match="simulated publish failure"):
            load_month(jan, 2025, 1, 1)
    finally:
        with psycopg2.connect(**options) as conn:
            with conn.cursor() as cur:
                cur.execute("DROP TRIGGER test_reject ON gold.trips")
                cur.execute("DROP FUNCTION gold.reject_test_insert()")
                cur.execute('SELECT "fare_amount" FROM gold.trips WHERE source_month=DATE \'2025-01-01\'')
                assert cur.fetchone()[0] == 99
