FROM apache/airflow:2.9.0

USER root
# Cài đặt Jave 17 JRE (cần thiết để khởi động Spark Session)
RUN apt-get update && \
    apt-get install -y --no-install-recommends openjdk-17-jre-headless libpq-dev gcc build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

USER airflow
# Cài đặt các thư viện phụ thuộc từng bước để tối ưu Docker cache & network retries
RUN pip install --no-cache-dir --retries 10 --timeout 1000 requests==2.32.4 psycopg2-binary
RUN pip install --no-cache-dir --retries 10 --timeout 1000 "dbt-postgres==1.8.0"
RUN pip install --no-cache-dir --retries 10 --timeout 1000 pyspark==3.5.1