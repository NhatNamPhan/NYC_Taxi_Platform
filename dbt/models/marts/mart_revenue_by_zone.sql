-- Mart model: mart_revenue_by_zone
-- Phân tích doanh thu, sản lượng chuyến đi và tiền tip theo khu vực đón khách (Zone)

SELECT
    l.zone AS pickup_zone,
    l.borough AS pickup_borough,
    COUNT(*) AS total_trips,
    ROUND(SUM(t.total_amount)::NUMERIC, 2) AS total_revenue,
    ROUND(SUM(t.fare_amount)::NUMERIC, 2) AS total_fare,
    ROUND(SUM(t.tip_amount)::NUMERIC, 2) AS total_tips,
    ROUND(AVG(t.tip_percentage)::NUMERIC, 2) AS avg_tip_percentage,
    ROUND(AVG(t.trip_distance)::NUMERIC, 2) AS avg_trip_distance,
    ROUND(AVG(t.trip_duration_min)::NUMERIC, 2) AS avg_duration_min
FROM {{ ref('fact_trips') }} t
JOIN {{ ref('dim_location') }} l ON t.pickup_location_id = l.location_id
GROUP BY 1, 2
ORDER BY total_revenue DESC
