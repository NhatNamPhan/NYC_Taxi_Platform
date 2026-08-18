-- Mart model: mart_kpi_summary
-- Pre-aggregated overall platform KPIs for instant dashboard loading (0.001s)

SELECT
    COUNT(*) AS total_trips,
    ROUND(SUM(total_amount)::NUMERIC, 2) AS total_revenue,
    ROUND(AVG(fare_amount)::NUMERIC, 2) AS avg_fare_amount,
    ROUND(AVG(tip_percentage)::NUMERIC, 2) AS avg_tip_percentage,
    ROUND(AVG(trip_distance)::NUMERIC, 2) AS avg_trip_distance
FROM {{ ref('fact_trips') }}
