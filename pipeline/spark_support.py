"""Spark configuration and month-local publication; source files are never modified."""
import json
import os
import platform
import shutil
import uuid
from pathlib import Path

from pipeline.config import DATA_DIR, PROJECT_ROOT


def create_spark(name, jdbc=False):
    from pyspark.sql import SparkSession

    if platform.system() == "Windows" and (PROJECT_ROOT / "hadoop").exists():
        os.environ.setdefault("HADOOP_HOME", str(PROJECT_ROOT / "hadoop"))
        os.environ["PATH"] += os.pathsep + str(PROJECT_ROOT / "hadoop" / "bin")
    builder = (SparkSession.builder.appName(name)
               .master(os.getenv("SPARK_MASTER", "local[2]"))
               .config("spark.driver.memory", os.getenv("SPARK_DRIVER_MEMORY", "2g"))
               .config("spark.sql.shuffle.partitions", os.getenv("SPARK_SHUFFLE_PARTITIONS", "8"))
               # TLC timestamp_ntz values are NYC wall-clock readings, not UTC instants.
               .config("spark.sql.session.timeZone", "America/New_York")
               .config("spark.sql.timestampType", "TIMESTAMP_NTZ"))
    if jdbc:
        builder = builder.config("spark.jars.packages", "org.postgresql:postgresql:42.7.3")
    session = builder.getOrCreate()
    session.sparkContext.setLogLevel("WARN")
    return session


def publish_parquet(df, destination):
    """Complete a month before swapping directories; restore the old month on failure.

    Requires a local filesystem, not an object-storage transaction. Airflow
    serializes pipeline runs. A process kill during rename may need recovery
    from the hidden .backup directory; it never affects other months.
    """
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex
    temporary = destination.with_name(f".{destination.name}.{token}.tmp")
    backup = destination.with_name(f".{destination.name}.{token}.backup")
    try:
        df.write.mode("errorifexists").parquet(str(temporary))
        if destination.exists():
            destination.rename(backup)
        try:
            temporary.rename(destination)
        except BaseException:
            if backup.exists():
                backup.rename(destination)
            raise
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    if backup.exists():
        shutil.rmtree(backup)


def write_quality_report(year, month, report):
    destination = DATA_DIR / "quality" / f"{year}-{month:02d}.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(temporary, destination)
