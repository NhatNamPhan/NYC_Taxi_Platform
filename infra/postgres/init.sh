#!/bin/sh
set -eu
psql --username "$POSTGRES_USER" --dbname postgres --set=ON_ERROR_STOP=1 \
  --set=warehouse_password="$WAREHOUSE_PASSWORD" \
  --set=airflow_password="$AIRFLOW_DB_PASSWORD" \
  --set=superset_password="$SUPERSET_DB_PASSWORD" \
  --set=reader_password="$BI_READER_PASSWORD" <<'SQL'
CREATE ROLE nyc_pipeline LOGIN PASSWORD :'warehouse_password';
CREATE ROLE airflow LOGIN PASSWORD :'airflow_password';
CREATE ROLE superset LOGIN PASSWORD :'superset_password';
CREATE ROLE bi_reader LOGIN PASSWORD :'reader_password';
CREATE DATABASE nyc_taxi OWNER nyc_pipeline;
CREATE DATABASE nyc_taxi_test OWNER nyc_pipeline;
CREATE DATABASE airflow OWNER airflow;
CREATE DATABASE superset OWNER superset;
REVOKE CONNECT ON DATABASE airflow FROM PUBLIC;
REVOKE CONNECT ON DATABASE superset FROM PUBLIC;
\connect nyc_taxi
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
CREATE SCHEMA gold AUTHORIZATION nyc_pipeline;
CREATE SCHEMA load_stage AUTHORIZATION nyc_pipeline;
CREATE SCHEMA staging AUTHORIZATION nyc_pipeline;
CREATE SCHEMA core AUTHORIZATION nyc_pipeline;
CREATE SCHEMA mart AUTHORIZATION nyc_pipeline;
CREATE SCHEMA reference AUTHORIZATION nyc_pipeline;
GRANT USAGE ON SCHEMA mart TO bi_reader;
ALTER DEFAULT PRIVILEGES FOR ROLE nyc_pipeline IN SCHEMA mart GRANT SELECT ON TABLES TO bi_reader;
SQL
