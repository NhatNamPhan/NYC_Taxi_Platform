-- Staging model: stg_zones
-- Direct read from taxi zone lookup

SELECT
    *
FROM {{ source('gold', 'taxi_zone_lookup') }}
