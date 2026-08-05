from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

# Cấu hình mặc định cho các task
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2026, 7, 21),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=3),
}

# Khởi tạo DAG
with DAG(
    'nyc_taxi_pipeline',
    default_args=default_args,
    description='End-to-end batch ETL pipeline for NYC Yellow Taxi',
    schedule_interval=None, # Chạy thủ công
    catchup=False,
) as dag:

    # Task 1: Tải dữ liệu thô
    download_data = BashOperator(
        task_id='download_data_bronze',
        bash_command='python /opt/airflow/ingestion/download_data.py',
    )

    # Task 2: Làm sạch dữ liệu (Bronze -> Silver)
    bronze_to_silver = BashOperator(
        task_id='spark_bronze_to_silver',
        bash_command='python /opt/airflow/spark/bronze_to_silver.py',
    )

    # Task 3: Làm giàu và nạp dữ liệu vào Postgres (Silver -> Gold)
    silver_to_gold = BashOperator(
        task_id='spark_silver_to_gold',
        bash_command='python /opt/airflow/spark/silver_to_gold.py',
    )

    # Task 4: Chạy dbt chuyển đổi các bảng Marts
    dbt_run = BashOperator(
        task_id='dbt_transform_marts',
        bash_command='cd /opt/airflow/dbt && dbt run --threads 4 --profiles-dir .',
    )

    # Định nghĩa luồng chạy tuần tự
    download_data >> bronze_to_silver >> silver_to_gold >> dbt_run
