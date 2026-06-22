-- Dimension model: dim_location
-- Unique locations with zone and borough info

SELECT
    location_id,
    zone,
    borough,
    service_zone
FROM {{ ref('stg_zones') }}
