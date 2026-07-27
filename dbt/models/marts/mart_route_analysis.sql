-- Mart model: mart_route_analysis
-- Phân tích các tuyến đường phổ biến (Pickup Zone -> Dropoff Zone)

SELECT
    pu.borough AS pickup_borough,
    pu.zone AS pickup_zone,
    drp.borough AS dropoff_borough,
    drp.zone AS dropoff_zone,
    CONCAT(pu.zone, ' -> ', drp.zone) AS route_name,
    COUNT(*) AS total_trips,
    ROUND(SUM(t.total_amount)::NUMERIC, 2) AS total_revenue,
    ROUND(AVG(t.fare_amount)::NUMERIC, 2) AS avg_fare_amount,
    ROUND(AVG(t.trip_distance)::NUMERIC, 2) AS avg_trip_distance,
    ROUND(AVG(t.trip_duration_min)::NUMERIC, 2) AS avg_duration_min,
    ROUND(AVG(t.speed_mph)::NUMERIC, 2) AS avg_speed_mph
FROM {{ ref('fact_trips') }} t
LEFT JOIN {{ ref('dim_location') }} pu ON t.pickup_location_id = pu.location_id
LEFT JOIN {{ ref('dim_location') }} drp ON t.dropoff_location_id = drp.location_id
GROUP BY 1, 2, 3, 4, 5
ORDER BY total_trips DESC










