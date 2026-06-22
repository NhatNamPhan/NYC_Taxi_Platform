-- Fact model: fact_trips
-- Core trip metrics joined with dimension keys

SELECT
    trip_id,
    pickup_location_id,
    dropoff_location_id,
    tpep_pickup_datetime  AS pickup_datetime,
    tpep_dropoff_datetime AS dropoff_datetime,
    total_amount,
    tip_amount,
    fare_amount,
    trip_distance,
    trip_duration_min,
    tip_percentage
FROM {{ ref('stg_trips') }}
