"""Enrich selected months and replace their warehouse contents through staging."""
import logging
from pyspark import StorageLevel
from pyspark.sql import functions as F

from ingestion.download_data import LOOKUP_PATH, validate_lookup
from pipeline.config import month_arguments, months, partition_path
from pipeline.spark_support import create_spark, publish_parquet
from pipeline.warehouse import load_month

LOG = logging.getLogger(__name__)


def enrich(df, zones):
    lookup = zones.select(F.col("LocationID").cast("int").alias("zone_id"),
                         F.col("Borough").alias("pickup_borough"),
                         F.col("Zone").alias("pickup_zone_name"), "service_zone")
    return (df.join(F.broadcast(lookup), df.PULocationID == lookup.zone_id, "left")
            .drop("zone_id")
            .withColumn("tip_percentage", F.col("tip_amount") / F.col("fare_amount") * 100)
            .withColumn("pickup_date", F.to_date("tpep_pickup_datetime"))
            .withColumn("pickup_hour", F.hour("tpep_pickup_datetime")))


def main(argv=None):
    args = month_arguments(__doc__, argv)
    validate_lookup(LOOKUP_PATH)
    spark = create_spark("NYC Taxi Silver to Gold", jdbc=True)
    try:
        zones = spark.read.option("header", True).csv(str(LOOKUP_PATH))
        for year, month in months(args.start_month, args.end_month):
            silver = spark.read.parquet(str(partition_path("silver", year, month)))
            if not {"trip_id", "source_month", "cbd_congestion_fee", "trip_duration_min", "speed_mph"}.issubset(silver.columns):
                raise ValueError("Legacy Silver schema; rerun Bronze to Silver for this month first")
            gold = enrich(silver, zones).persist(StorageLevel.DISK_ONLY)
            try:
                count = gold.count()
                if count == 0:
                    raise ValueError("Refusing to publish an empty month")
                if gold.filter(F.col("pickup_zone_name").isNull()).limit(1).count():
                    raise ValueError("Missing zone lookup mapping")
                publish_parquet(gold, partition_path("gold", year, month))
                load_month(gold, year, month, count)
                LOG.info("Published %s-%02d: %s trips", year, month, count)
            finally:
                gold.unpersist()
    finally:
        spark.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
