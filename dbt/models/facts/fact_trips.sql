-- Fact model: fact_trips
-- Core trip metrics joined with dimension keys

SELECT
    trip_id,
    vendor_id,
    ratecode_id,
    payment_type,
    pickup_location_id,
    dropoff_location_id,
    tpep_pickup_datetime  AS pickup_datetime,
    tpep_dropoff_datetime AS dropoff_datetime,
    passenger_count,
    total_amount,
    tip_amount,
    fare_amount,
    tolls_amount,
    airport_fee,
    trip_distance,
    trip_duration_min,
    tip_percentage,
    speed_mph
FROM {{ ref('stg_trips') }}
