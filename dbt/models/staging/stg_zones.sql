-- Staging model: stg_zones
-- Đọc dữ liệu từ seed file taxi_zone_lookup

SELECT
   "LocationID" AS location_id,
   "Borough" AS borough,
   "Zone" AS zone,
   "service_zone" AS service_zone
FROM {{ ref('taxi_zone_lookup') }}