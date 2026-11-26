"""Normalize and validate each source month, retaining rejected rows for audit."""
from datetime import date
import logging
import os

from pyspark import StorageLevel
from pyspark.sql import functions as F

from pipeline.config import month_arguments, months, next_month, partition_path
from pipeline.spark_support import create_spark, publish_parquet, write_quality_report

LOG = logging.getLogger(__name__)
TYPES = {
    "VendorID": "int", "tpep_pickup_datetime": "timestamp_ntz",
    "tpep_dropoff_datetime": "timestamp_ntz", "passenger_count": "int",
    "trip_distance": "double", "RatecodeID": "int", "store_and_fwd_flag": "string",
    "PULocationID": "int", "DOLocationID": "int", "payment_type": "int",
    **{name: "decimal(18,2)" for name in (
        "fare_amount", "extra", "mta_tax", "tip_amount", "tolls_amount",
        "improvement_surcharge", "total_amount", "congestion_surcharge", "Airport_fee",
        "cbd_congestion_fee")},
}


def normalize(df, year, month):
    required = set(TYPES) - ({"cbd_congestion_fee"} if year < 2025 else set())
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Source schema is missing required columns: {sorted(missing)}")
    unexpected = set(df.columns) - set(TYPES)
    if unexpected:
        raise ValueError(f"New source columns require a schema update: {sorted(unexpected)}")
    if "cbd_congestion_fee" not in df.columns:
        df = df.withColumn("cbd_congestion_fee", F.lit(0))
    df = df.select(*[F.col(name).cast(dtype).alias(name) for name, dtype in TYPES.items()])
    # Grain: one distinct canonical source record in a source month. Raw retains duplicates.
    fingerprint = F.to_json(F.struct(*[F.col(name) for name in TYPES]), {"ignoreNullFields": "false"})
    return (df.withColumn("source_month", F.lit(date(year, month, 1)).cast("date"))
            .withColumn("trip_id", F.sha2(F.concat(F.lit(f"{year}-{month:02d}|"), fingerprint), 256)))


def classify(df, year, month):
    start = date(year, month, 1)
    duration = (F.unix_timestamp("tpep_dropoff_datetime") - F.unix_timestamp("tpep_pickup_datetime")) / 60.0
    max_speed = float(os.getenv("MAX_SPEED_MPH", "120"))
    max_duration = float(os.getenv("MAX_DURATION_MIN", "1440"))
    rules = {
        "invalid_vendor": F.col("VendorID").isNull() | (F.col("VendorID") <= 0),
        "invalid_pickup_location": ~F.col("PULocationID").between(1, 265),
        "invalid_dropoff_location": ~F.col("DOLocationID").between(1, 265),
        "pickup_outside_source_month": ~((F.col("tpep_pickup_datetime") >= F.lit(start)) &
                                         (F.col("tpep_pickup_datetime") < F.lit(next_month(start)))),
        "invalid_duration": ~duration.between(1.0 / 60, max_duration),
        "invalid_distance": ~F.col("trip_distance").between(0.001, 500) | F.isnan("trip_distance"),
        "implausible_speed": (F.col("trip_distance") / (duration / 60)) > max_speed,
        "invalid_fare": ~((F.col("fare_amount") > 0) & (F.col("fare_amount") < 1000)),
        "invalid_tip": F.col("tip_amount") < 0,
        "invalid_total": F.col("total_amount") <= 0,
        # Unknown passenger counts (null/0) do not invalidate an otherwise valid trip.
        "invalid_passengers": F.col("passenger_count").isNotNull() & ~F.col("passenger_count").between(0, 8),
    }
    reasons = [F.when(F.coalesce(condition, F.lit(True)), F.lit(name)) for name, condition in rules.items()]
    return (df.withColumn("rejection_reasons", F.filter(F.array(*reasons), lambda reason: reason.isNotNull()))
            .withColumn("trip_duration_min", duration)
            .withColumn("speed_mph", F.col("trip_distance") / (duration / 60)))


def process_month(spark, year, month):
    path = partition_path("bronze", year, month) / f"yellow_tripdata_{year}-{month:02d}.parquet"
    classified = classify(normalize(spark.read.parquet(str(path)), year, month), year, month).persist(StorageLevel.DISK_ONLY)
    try:
        input_rows = classified.count()
        invalid = classified.filter(F.size("rejection_reasons") > 0)
        valid = classified.filter(F.size("rejection_reasons") == 0)
        accepted = valid.drop("rejection_reasons").dropDuplicates(["trip_id"]).persist(StorageLevel.DISK_ONLY)
        try:
            accepted_rows = accepted.count()
            rejected_rows = invalid.count()
            duplicates = input_rows - rejected_rows - accepted_rows
            reasons = {row["reason"]: row["count"] for row in invalid.select(F.explode("rejection_reasons").alias("reason")).groupBy("reason").count().collect()}
            report = {"source_month": f"{year}-{month:02d}", "input_rows": input_rows,
                      "accepted_rows": accepted_rows, "rejected_rows": rejected_rows,
                      "duplicate_rows": duplicates, "reasons": reasons, "schema_version": 2}
            write_quality_report(year, month, report)
            LOG.info("Quality: %s", report)
            if accepted_rows == 0:
                raise ValueError("No accepted trips; refusing to replace a published month")
            publish_parquet(invalid, partition_path("quarantine", year, month))
            publish_parquet(accepted, partition_path("silver", year, month))
        finally:
            accepted.unpersist()
    finally:
        classified.unpersist()


def main(argv=None):
    args = month_arguments(__doc__, argv)
    spark = create_spark("NYC Taxi Bronze to Silver")
    try:
        for year, month in months(args.start_month, args.end_month):
            process_month(spark, year, month)
    finally:
        spark.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
