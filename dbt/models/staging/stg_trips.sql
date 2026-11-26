-- The canonical record ID is generated in Silver, where all source fields are available.
SELECT
    trip_id, source_month, pickup_date, pickup_hour,
    "VendorID" AS vendor_id,
    tpep_pickup_datetime AS pickup_datetime,
    tpep_dropoff_datetime AS dropoff_datetime,
    passenger_count, trip_distance,
    "RatecodeID" AS ratecode_id,
    store_and_fwd_flag,
    "PULocationID" AS pickup_location_id,
    "DOLocationID" AS dropoff_location_id,
    payment_type, fare_amount, extra, mta_tax, tip_amount, tolls_amount,
    improvement_surcharge, total_amount, congestion_surcharge,
    "Airport_fee" AS airport_fee, cbd_congestion_fee,
    trip_duration_min, tip_percentage, speed_mph
FROM {{ source('gold', 'trips') }}
