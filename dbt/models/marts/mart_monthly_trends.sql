-- Mart model: mart_monthly_trends
-- Month-over-month comparison 2024 vs 2025

SELECT
    dt.year,
    dt.month,
    COUNT(*)                             AS trip_count,
    ROUND(SUM(t.total_amount)::NUMERIC, 2) AS total_revenue,
    ROUND(AVG(t.trip_distance)::NUMERIC, 2) AS avg_distance
FROM {{ ref('fact_trips') }} t
JOIN {{ ref('dim_time') }} dt ON t.pickup_datetime = dt.datetime_id
GROUP BY dt.year, dt.month
ORDER BY dt.year, dt.month
