FROM apache/airflow:2.9.3-python3.11
USER root
RUN apt-get update && apt-get install -y --no-install-recommends openjdk-17-jre-headless \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
COPY dbt/requirements.txt /tmp/dbt-requirements.txt
# dbt and Airflow require different protobuf/telemetry dependency families.
RUN python -m venv /opt/dbt-venv \
    && /opt/dbt-venv/bin/pip install --no-cache-dir -r /tmp/dbt-requirements.txt \
    && ln -s /opt/dbt-venv/bin/dbt /usr/local/bin/dbt
USER airflow
COPY requirements.txt /tmp/requirements.txt
# Keep Airflow fixed; dbt runs through its isolated interpreter above.
RUN pip install --no-cache-dir "apache-airflow==2.9.3" -r /tmp/requirements.txt
WORKDIR /opt/airflow
