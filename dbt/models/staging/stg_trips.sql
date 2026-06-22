-- Staging model: stg_trips
-- Direct read from gold.trips with column aliasing

SELECT
    *
FROM {{ source('gold', 'trips') }}
