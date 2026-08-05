-- Mart model: mart_airport_vs_city
-- Phân tích và so sánh các chuyến đi Sân bay (JFK, LaGuardia, Newark) vs Chuyến đi Nội thành

SELECT
    CASE 
        WHEN t.ratecode_id = 2 THEN 'JFK Airport'
        WHEN t.ratecode_id = 3 THEN 'Newark Airport'
        WHEN t.ratecode_id = 4 THEN 'Nassau/Westchester'
        WHEN l.zone LIKE '%Airport%' OR l.zone LIKE '%JFK%' OR l.zone LIKE '%LaGuardia%' THEN 'Airport Trip'
        ELSE 'City Trip'
    END AS trip_type,
    l.borough AS pickup_borough,
    COUNT(*) AS total_trips,
    ROUND(SUM(t.total_amount)::NUMERIC, 2) AS total_revenue,
    ROUND(SUM(t.airport_fee)::NUMERIC, 2) AS total_airport_fees,
    ROUND(AVG(t.fare_amount)::NUMERIC, 2) AS avg_fare_amount,
    ROUND(AVG(t.trip_distance)::NUMERIC, 2) AS avg_trip_distance,
    ROUND(AVG(t.trip_duration_min)::NUMERIC, 2) AS avg_duration_min,
    ROUND(AVG(t.tip_percentage)::NUMERIC, 2) AS avg_tip_percentage
FROM {{ ref('fact_trips') }} t
LEFT JOIN {{ ref('dim_location') }} l ON t.pickup_location_id = l.location_id
GROUP BY 1, 2
ORDER BY total_revenue DESC

