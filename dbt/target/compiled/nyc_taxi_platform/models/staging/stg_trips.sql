-- Staging model: stg_trips
-- Đọc dữ liệu từ nguồn gold.trips và chuẩn hóa tên cột

SELECT 
    -- Tạo mã ID chuyến đi duy nhất (do dữ liệu thô không có khóa chính)
    md5(CONCAT(
        COALESCE(CAST("VendorID" AS VARCHAR), ''),
        COALESCE(CAST("tpep_pickup_datetime" AS VARCHAR), ''),
        COALESCE(CAST("PULocationID" AS VARCHAR), '')
    )) AS trip_id,

    "VendorID" AS vendor_id,
    "tpep_pickup_datetime" AS tpep_pickup_datetime,
    "tpep_dropoff_datetime" AS tpep_dropoff_datetime,
    "passenger_count" AS passenger_count,
    "trip_distance" AS trip_distance,
    "RatecodeID" AS ratecode_id,
    "store_and_fwd_flag" AS store_and_fwd_flag,
    "PULocationID" AS pickup_location_id,
    "DOLocationID" AS dropoff_location_id,
    "payment_type" AS payment_type,
    "fare_amount" AS fare_amount,
    "extra" AS extra,
    "mta_tax" AS mta_tax,
    "tip_amount" AS tip_amount,
    "tolls_amount" AS tolls_amount,
    "improvement_surcharge" AS improvement_surcharge,
    "total_amount" AS total_amount,
    "congestion_surcharge" AS congestion_surcharge,
    "Airport_fee" AS airport_fee,
    "pickup_borough" AS pickup_borough,
    "pickup_zone_name" AS pickup_zone_name,
    "service_zone" AS service_zone,
    "trip_duration_min" AS trip_duration_min,
    "tip_percentage" AS tip_percentage,
    "speed_mph" AS speed_mph
FROM "nyc_taxi"."gold"."trips"