-- Mart model: mart_hourly_demand
-- Phân tích nhu cầu chuyến đi, tốc độ di chuyển và thời gian theo 24 giờ trong ngày

SELECT
    EXTRACT(HOUR FROM t.pickup_datetime) AS pickup_hour,
    l.borough AS pickup_borough,
    COUNT(*) AS trip_count,
    ROUND(AVG(t.total_amount)::NUMERIC, 2) AS avg_total_amount,
    ROUND(AVG(t.trip_distance)::NUMERIC, 2) AS avg_trip_distance,
    ROUND(AVG(t.trip_duration_min)::NUMERIC, 2) AS avg_duration_min,
    ROUND(AVG(t.speed_mph)::NUMERIC, 2) AS avg_speed_mph
FROM {{ ref('fact_trips') }} t
LEFT JOIN {{ ref('dim_location') }} l ON t.pickup_location_id = l.location_id
GROUP BY 1, 2
ORDER BY 1, 2
