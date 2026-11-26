from decimal import Decimal
import pytest

from spark.bronze_to_silver import normalize, classify, process_month


def test_distinct_trips_no_longer_share_id_and_ids_are_stable(raw_frame, source_row):
    other = {**source_row, "DOLocationID": "158", "fare_amount": "7.20"}
    source = raw_frame([source_row, other])
    first = {r.trip_id for r in normalize(source, 2025, 1).collect()}
    again = {r.trip_id for r in normalize(source.repartition(2), 2025, 1).collect()}
    assert len(first) == 2
    assert first == again


def test_new_fee_is_preserved_and_2024_default_is_zero(raw_frame, source_row):
    assert normalize(raw_frame([source_row]), 2025, 1).first().cbd_congestion_fee == Decimal("2.50")
    old = {k: v for k, v in source_row.items() if k != "cbd_congestion_fee"}
    assert normalize(raw_frame([old]), 2024, 1).first().cbd_congestion_fee == Decimal("0.00")
    with pytest.raises(ValueError, match="cbd_congestion_fee"):
        normalize(raw_frame([old]), 2025, 1)


def test_unexpected_schema_change_fails_explicitly(raw_frame, source_row):
    with pytest.raises(ValueError, match="New source columns"):
        normalize(raw_frame([{**source_row, "future_fee": "3.00"}]), 2025, 1)


@pytest.mark.parametrize("changes,reason", [
    ({"tpep_dropoff_datetime": "2025-01-01 00:09:08"}, "invalid_duration"),
    ({"tpep_dropoff_datetime": None}, "invalid_duration"),
    ({"PULocationID": "999"}, "invalid_pickup_location"),
    ({"tpep_pickup_datetime": "2024-12-31 23:59:59"}, "pickup_outside_source_month"),
    ({"trip_distance": "NaN"}, "invalid_distance"),
    ({"trip_distance": "400"}, "implausible_speed"),
    ({"fare_amount": "invalid"}, "invalid_fare"),
])
def test_rejections_have_auditable_reasons(raw_frame, source_row, changes, reason):
    row = classify(normalize(raw_frame([{**source_row, **changes}]), 2025, 1), 2025, 1).first()
    assert reason in row.rejection_reasons


def test_unknown_passengers_are_kept(raw_frame, source_row):
    frame = raw_frame([{**source_row, "passenger_count": None}])
    assert classify(normalize(frame, 2025, 1), 2025, 1).first().rejection_reasons == []


def test_month_publication_reconciles_duplicates_and_keeps_other_months(spark, raw_frame, source_row, tmp_path, monkeypatch):
    import json
    import pipeline.config as config
    import pipeline.spark_support as support
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(support, "DATA_DIR", tmp_path)
    source = config.partition_path("bronze", 2025, 1) / "yellow_tripdata_2025-01.parquet"
    raw_frame([source_row, source_row, {**source_row, "DOLocationID": "999"}]).write.parquet(str(source))
    other = config.partition_path("silver", 2025, 2)
    other.mkdir(parents=True)
    (other / "sentinel").write_text("published February")
    process_month(spark, 2025, 1)
    process_month(spark, 2025, 1)
    result = spark.read.parquet(str(config.partition_path("silver", 2025, 1)))
    assert result.count() == 1
    report = json.loads((tmp_path / "quality/2025-01.json").read_text())
    assert report["input_rows"] == report["accepted_rows"] + report["rejected_rows"] + report["duplicate_rows"]
    assert report["duplicate_rows"] == 1
    assert spark.read.parquet(str(config.partition_path("quarantine", 2025, 1))).count() == 1
    assert (other / "sentinel").read_text() == "published February"
