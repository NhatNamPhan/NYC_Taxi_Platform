# NYC Taxi Analytics Platform

Monthly batch analytics for NYC Yellow Taxi records using **Spark, PostgreSQL, dbt, Airflow and Apache Superset**.

```text
TLC Parquet -> Bronze -> Silver + quarantine -> Gold Parquet
                                      -> JDBC staging -> gold.trips
                                      -> dbt staging/core/mart -> Superset
```

## Quick start (Windows / PowerShell)

Requirements: Docker Desktop with Linux containers, Docker Compose, Python 3.10+ for environment generation. Allow at least 6-8 GB RAM for the complete local stack; start with one month.

```powershell
python scripts/setup_env.py
docker compose --env-file .env.compose up --build -d
```

This creates **new** container databases in the `nyc-taxi-platform_postgres_data` volume. Your existing PostgreSQL on port 5433 and existing `.env` are not used or migrated. The warehouse is exposed at `localhost:5434` by default.

| Service | URL | Login |
|---|---|---|
| Airflow | http://localhost:8080 | `admin`, password `AIRFLOW_ADMIN_PASSWORD` in `.env.compose` |
| Superset | http://localhost:8088 | `admin`, password `SUPERSET_ADMIN_PASSWORD` in `.env.compose` |

Secrets are generated locally in the ignored `.env.compose`. Keep that file between restarts. Database bootstrap runs only when the PostgreSQL volume is first created; editing a password in the file alone does not rotate an existing database password.

## Run a selected month

Open Airflow, unpause `nyc_taxi_pipeline`, then trigger it with `start_month=2025-01`, `end_month=2025-01`. Alternatively:

```powershell
docker compose --env-file .env.compose exec airflow-scheduler python -m pipeline.trigger --start-month 2025-01 --end-month 2025-01
```

For a direct foreground run without waiting for the scheduler:

```powershell
docker compose --env-file .env.compose exec airflow-scheduler python -m ingestion.download_data --start-month 2025-01 --end-month 2025-01
docker compose --env-file .env.compose exec airflow-scheduler python -m spark.bronze_to_silver --start-month 2025-01 --end-month 2025-01
docker compose --env-file .env.compose exec airflow-scheduler python -m spark.silver_to_gold --start-month 2025-01 --end-month 2025-01
docker compose --env-file .env.compose exec -e PIPELINE_START_MONTH=2025-01 -e PIPELINE_END_MONTH=2025-01 airflow-scheduler dbt build --project-dir /opt/airflow/dbt --profiles-dir /opt/airflow/dbt
```

Do not run the foreground workflow while a DAG run is writing the same local data. Airflow itself serializes DAG runs and tasks. Select `2024-01` through `2025-12` for the full historical rebuild after the single-month run succeeds.

## Create the Superset dashboards

After a successful `dbt build`:

```powershell
docker compose --env-file .env.compose --profile tools run --rm superset-assets
```

The command connects Superset to the warehouse with **`bi_reader`**, which can only select from `mart`, and provisions three dashboards:

- Revenue overview: revenue, trip count, average fare, recorded credit-card tip percentage and monthly trend.
- Demand and locations: hourly demand, top zones and day-of-week totals.
- Routes and payments: top routes, airport/city comparison and payment methods.

Every dashboard has a month-range filter. Run provisioning again to update the managed charts; it overwrites edits to those managed charts/layouts. Duplicate a dashboard before customizing it independently. See [DASHBOARD_GUIDE.md](DASHBOARD_GUIDE.md) for metric definitions and filters.

To provision clearly labeled **synthetic validation dashboards** against the smoke-test database instead of the real warehouse:

```powershell
docker compose --env-file .env.compose --profile tools run --rm -e BI_DATABASE_NAME=nyc_taxi_test -e SUPERSET_ASSET_PREFIX=validation superset-assets
docker compose --env-file .env.compose --profile tools run --rm --no-deps superset-assets python /app/verify_superset.py
```

Run the smoke test below first. Validation pages use `/superset/dashboard/validation-overview/`, `validation-demand/` and `validation-routes/`, and display `Synthetic demo` in their titles. Their database is separate from the real warehouse. API verification checks 12 chart queries, the month filter and BI access restrictions; it does not perform screenshot/visual QA. Re-running warehouse tests can reset this disposable test data.

## Data contracts and quality

- **Grain:** one distinct canonical source record within a source month. `trip_id` is SHA-256 of the source month and all canonical source fields, not vendor/pickup/location alone. Exact canonical duplicates collapse in Silver and are counted in the report; Bronze preserves all original rows. TLC has no reliable individual trip ID, so identical real-world trips cannot be distinguished from duplicate records. Monetary fields normalize to two decimal places.
- Each month is read separately. Missing required columns and unexpected new columns fail explicitly. `cbd_congestion_fee` is preserved for 2025+ and filled with zero for pre-2025 files.
- Timestamps remain **NYC local wall-clock values** (`timestamp_ntz`); they are not asserted to be UTC instants. DST ambiguity in the published source cannot be reconstructed reliably.
- The analytical population is positive-fare, positive-total trips with plausible distance/duration/speed. Refunds, zero fares, invalid locations, invalid timestamps and outliers go to quarantine; this is not a complete financial ledger. Null/zero passenger counts are retained as unknown.
- `data/quality/YYYY-MM.json` records input, accepted, rejected and duplicate counts plus rejection reasons. Reason counts overlap when a row violates several rules. `input = accepted + rejected + duplicates`.
- `data/quarantine/year=YYYY/month=MM` retains invalid rows and their reasons.
- Location IDs 264/265 represent unknown/outside NYC and remain valid reference members.
- Cash tips are not recorded by TLC. Card tip percentage is `100 * card_tips / card_fare`, not an estimate of cash tipping.

## Safe monthly replacement

Silver and Gold are written to temporary directories before replacing only the selected month. Filesystem publication is a local rename workflow, not an object-store ACID transaction. A process kill between renames can leave a hidden `.backup` directory; restore it before retrying if necessary.

JDBC writes to a unique `load_stage` table first. The loader checks row count, unique IDs and month bounds, then replaces the warehouse month and updates `gold.load_manifest` in **one PostgreSQL transaction**. A failed insert rolls back the replacement. A hard-killed loader may leave an unused staging table; published data remains unchanged.

Gold Parquet and PostgreSQL are separate publications: a failed warehouse load can leave newer Gold Parquet, while the last committed warehouse remains readable. Retry the same month to reconcile. BI reads only dbt marts.

Facts and marts are incremental. Their selected-month delete and insert run in the same dbt model transaction, including records removed by a rerun. Other months remain intact. **The entire dbt build is not a cross-model transaction**: during a failed multi-model build, BI may briefly see different model versions; only consider the release complete after all tests pass. `dbt build --full-refresh` rebuilds all warehouse history, not just the selected months.

Schemas: `gold` (validated warehouse source), `load_stage` (temporary writes), `reference` (zone seed), `staging` (views), `core` (facts/dimensions), `mart` (BI). `dim_time` contains 24 hours; `dim_date` contains one row per date.

## Tests

Tests use synthetic data and the separate `nyc_taxi_test` database; they do not reload your historical data.

```powershell
docker compose --env-file .env.compose run --rm -e RUN_WAREHOUSE_TESTS=1 airflow-scheduler bash -c 'pip install pytest==8.3.5 && python -m pytest -q tests'
```

Coverage includes interrupted/failed downloads, worker error propagation, schema evolution, ID stability, rejected rows, monthly idempotence and PostgreSQL rollback. `dbt build` additionally runs key/relationship tests and reconciles every mart against fact counts/revenue and warehouse load manifests.

For a complete small end-to-end verification (two synthetic months, then a rerun that removes a January trip while preserving December):

```powershell
docker compose --env-file .env.compose run --rm -e DB_NAME=nyc_taxi_test -e TAXI_DATA_DIR=/tmp/taxi-smoke airflow-scheduler python -m tests.smoke_pipeline
```

This command resets schemas in **nyc_taxi_test only**. The smoke script refuses the normal warehouse and data directory.

## Layout

```text
pipeline/           shared paths, month selection, Spark publication, warehouse loader
ingestion/          atomic validated downloads
spark/              month-local normalization, quarantine and enrichment
dags/               parameterized sequential Airflow workflow
dbt/models/         staging, core dimensions/fact and 8 monthly-grain marts
dbt/seeds/          versioned 265-location reference
infra/postgres/     initial databases, schemas and least-privilege BI role
infra/superset/     configuration, initialization and dashboard provisioning
tests/              regression and integration tests
scripts/setup_env.py generated local secrets without modifying existing .env
```

Adjust resources and quality thresholds in `.env.compose`. Local Docker setup is intended for development/portfolio use. An internet-facing deployment needs TLS, a supported orchestrator/runtime upgrade plan, backups and environment-specific access controls.

Official references: [Superset Docker images](https://superset.apache.org/admin-docs/installation/docker-builds/), [TLC data dictionary](https://www.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf).
