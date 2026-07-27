-- Mart model: mart_day_of_week
-- Phân tích nhu cầu chuyến đi và hiệu suất doanh thu theo các ngày trong tuần & Ngày tuần vs Cuối tuần

SELECT
    dt.day_of_week,
    dt.day_name,
    dt.is_weekend,
    CASE
        WHEN dt.is_weekend THEN 'Weekend'
        ELSE 'Weekday'
    END AS day_type,
    COUNT(*) AS total_trips,
    ROUND(SUM(t.total_amount)::NUMERIC, 2) AS total_revenue,
    ROUND(AVG(t.fare_amount)::NUMERIC, 2) AS avg_fare_amount,
    ROUND(AVG(t.trip_distance)::NUMERIC, 2) AS avg_trip_distance,
    ROUND(AVG(t.trip_duration_min)::NUMERIC, 2) AS avg_duration_min,
    ROUND(AVG(t.tip_percentage)::NUMERIC, 2) AS avg_tip_percentage
FROM {{ ref('fact_trips') }} t
JOIN {{ ref('dim_time') }} dt ON t.pickup_datetime = dt.datetime_id
GROUP BY 1, 2, 3, 4
ORDER BY dt.day_of_week ASC