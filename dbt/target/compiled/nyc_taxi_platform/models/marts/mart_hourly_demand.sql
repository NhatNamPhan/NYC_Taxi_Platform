-- Mart model: mart_hourly_demand
-- Phân tích nhu cầu chuyến đi theo giờ và quận/huyện

SELECT
    EXTRACT(HOUR FROM t.pickup_datetime) AS pickup_hour,
    l.borough AS pickup_borough,
    COUNT(*) AS trip_count,
    ROUND(AVG(t.total_amount)::NUMERIC, 2) AS avg_total_amount,
    ROUND(AVG(t.trip_distance)::NUMERIC, 2) AS avg_trip_distance
FROM "nyc_taxi"."gold"."fact_trips" t
LEFT JOIN "nyc_taxi"."gold"."dim_location" l ON t.pickup_location_id = l.location_id
GROUP BY 1, 2
ORDER BY 1, 2