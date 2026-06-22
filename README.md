# NYC Taxi Analytics Platform

End-to-end batch ETL pipeline for NYC Yellow Taxi trip data (2024–2025).

## Architecture

**Medallion Architecture**: Bronze → Silver → Gold → PostgreSQL → dbt → Metabase

## Tech Stack

| Layer | Tool |
|---|---|
| Processing | Apache Spark (PySpark) |
| Orchestration | Apache Airflow |
| Transformation | dbt |
| Storage | Parquet / Medallion Architecture |
| Warehouse | PostgreSQL |
| Visualization | Metabase |

## Project Structure

```
nyc_taxi_platform/
├── dags/
│   └── nyc_taxi_pipeline.py
├── spark/
│   ├── bronze_to_silver.py
│   └── silver_to_gold.py
├── dbt/
│   ├── models/
│   │   ├── staging/
│   │   ├── dimensions/
│   │   ├── facts/
│   │   └── marts/
│   └── dbt_project.yml
├── ingestion/
│   └── download_data.py
├── data/
│   ├── bronze/
│   ├── silver/
│   └── gold/
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start services
docker-compose up -d

# 3. Download data
python ingestion/download_data.py

# 4. Run pipeline
airflow dags trigger nyc_taxi_pipeline
```

## Dataset

- **Source**: NYC TLC Yellow Taxi Trip Records
- **Period**: January 2024 – December 2025
- **Files**: 24 monthly Parquet files (~8–10 GB)
- **Estimated rows**: ~20–25 million trips
