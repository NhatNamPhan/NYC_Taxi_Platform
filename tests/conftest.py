import os
import pytest


@pytest.fixture(scope="session")
def spark():
    from pipeline.spark_support import create_spark
    session = create_spark("Taxi regression tests", jdbc=os.getenv("RUN_WAREHOUSE_TESTS") == "1")
    yield session
    session.stop()


@pytest.fixture
def source_row():
    from spark.bronze_to_silver import TYPES
    row = {name: "0" for name in TYPES}
    row.update(VendorID="1", tpep_pickup_datetime="2025-01-01 00:09:08",
               tpep_dropoff_datetime="2025-01-01 00:31:26", passenger_count="1",
               trip_distance="4.5", RatecodeID="1", store_and_fwd_flag="N",
               PULocationID="158", DOLocationID="233", payment_type="1",
               fare_amount="20.50", tip_amount="4.10", total_amount="28.10",
               cbd_congestion_fee="2.50")
    return row


@pytest.fixture
def raw_frame(spark):
    def create(rows):
        names = list(rows[0])
        return spark.createDataFrame([tuple(row[name] for name in names) for row in rows],
                                     schema=", ".join(f"`{name}` string" for name in names))
    return create
