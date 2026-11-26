"""Stage JDBC writes, validate, then replace one warehouse month transactionally."""
from datetime import date
import os
import uuid

import psycopg2
from psycopg2 import sql

from pipeline.config import next_month


def connection_options():
    password = os.environ.get("DB_PASSWORD")
    if not password:
        raise ValueError("DB_PASSWORD must be configured")
    return dict(host=os.getenv("DB_HOST", "localhost"), port=int(os.getenv("DB_PORT", "5434")),
                dbname=os.getenv("DB_NAME", "nyc_taxi"), user=os.getenv("DB_USER", "nyc_pipeline"),
                password=password, connect_timeout=15)


def load_month(df, year, month, expected_rows):
    options = connection_options()
    stage_name = f"trips_{uuid.uuid4().hex}"
    stage = sql.Identifier("load_stage", stage_name)
    target = sql.Identifier("gold", "trips")
    start = date(year, month, 1)
    run_id = uuid.uuid4().hex
    conn = psycopg2.connect(**options)
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("CREATE SCHEMA IF NOT EXISTS load_stage")
        partitions = int(os.getenv("JDBC_PARTITIONS", "2"))
        (df.repartition(partitions).write.format("jdbc")
         .option("url", f"jdbc:postgresql://{options['host']}:{options['port']}/{options['dbname']}")
         .option("dbtable", f"load_stage.{stage_name}")
         .option("user", options["user"]).option("password", options["password"])
         .option("driver", "org.postgresql.Driver").option("batchsize", "10000")
         .option("numPartitions", str(partitions)).mode("errorifexists").save())
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql.SQL("SELECT COUNT(*), COUNT(DISTINCT trip_id), MIN(source_month), MAX(source_month) FROM {}").format(stage))
                count, unique, minimum, maximum = cursor.fetchone()
                if count != expected_rows or unique != count or minimum != start or maximum != start:
                    raise ValueError("Staging validation failed; the published warehouse month was not changed")
                cursor.execute("SELECT pg_advisory_xact_lock(hashtext('nyc_taxi_monthly_load'))")
                cursor.execute("CREATE SCHEMA IF NOT EXISTS gold")
                cursor.execute(sql.SQL("CREATE TABLE IF NOT EXISTS {} (LIKE {} INCLUDING DEFAULTS) PARTITION BY RANGE (source_month)").format(target, stage))
                cursor.execute("SELECT column_name, data_type, udt_name FROM information_schema.columns WHERE table_schema='gold' AND table_name='trips' ORDER BY ordinal_position")
                target_schema = cursor.fetchall()
                cursor.execute("SELECT column_name, data_type, udt_name FROM information_schema.columns WHERE table_schema='load_stage' AND table_name=%s ORDER BY ordinal_position", (stage_name,))
                if cursor.fetchall() != target_schema:
                    raise ValueError("Warehouse schema differs. Use the new Compose warehouse or perform an explicit migration; legacy tables will not be overwritten.")
                cursor.execute(sql.SQL("CREATE TABLE IF NOT EXISTS {} PARTITION OF {} FOR VALUES FROM ({}) TO ({})").format(
                    sql.Identifier("gold", f"trips_{year}_{month:02d}"), target,
                    sql.Literal(start), sql.Literal(next_month(start))))
                cursor.execute(sql.SQL("CREATE UNIQUE INDEX IF NOT EXISTS trips_month_trip_id ON {} (source_month, trip_id)").format(target))
                cursor.execute(sql.SQL("DELETE FROM {} WHERE source_month = %s").format(target), (start,))
                columns = sql.SQL(", ").join(sql.Identifier(name) for name in df.columns)
                cursor.execute(sql.SQL("INSERT INTO {} ({}) SELECT {} FROM {}").format(target, columns, columns, stage))
                if cursor.rowcount != expected_rows:
                    raise ValueError("Warehouse inserted row count differs from the accepted month")
                cursor.execute("""CREATE TABLE IF NOT EXISTS gold.load_manifest (
                    source_month DATE PRIMARY KEY, row_count BIGINT NOT NULL,
                    loaded_at TIMESTAMPTZ NOT NULL, run_id TEXT NOT NULL,
                    schema_version INTEGER NOT NULL)""")
                cursor.execute("""INSERT INTO gold.load_manifest VALUES (%s, %s, CURRENT_TIMESTAMP, %s, 2)
                    ON CONFLICT (source_month) DO UPDATE SET row_count=EXCLUDED.row_count,
                    loaded_at=EXCLUDED.loaded_at, run_id=EXCLUDED.run_id, schema_version=2""", (start, expected_rows, run_id))
    finally:
        # A failed Spark write can leave a partial staging table; never publish it.
        try:
            conn.rollback()
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(stage))
        finally:
            conn.close()
