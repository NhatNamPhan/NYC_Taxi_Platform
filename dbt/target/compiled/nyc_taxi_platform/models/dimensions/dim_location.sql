-- Dimension model: dim_location
-- Unique locations with zone and borough info

SELECT
    location_id,
    zone,
    borough,
    service_zone
FROM "nyc_taxi"."gold"."stg_zones"