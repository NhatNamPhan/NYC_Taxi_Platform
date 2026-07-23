-- Mart model: mart_payment_insights
-- Phân tích doanh thu và hành vi tip theo phương thức thanh toán

SELECT
    CASE
        WHEN s.payment_type = 1 THEN 'Credit Card'
        WHEN s.payment_type = 2 THEN 'Cash'
        WHEN s.payment_type = 3 THEN 'No Charge'
        WHEN s.payment_type = 4 THEN 'Dispute'
        ELSE 'Unknown'
    END AS payment_method,
    l.borough AS pickup_borough,
    COUNT(*) AS total_trips,
    ROUND(SUM(t.total_amount)::NUMERIC, 2) AS total_revenue,
    ROUND(SUM(t.tip_amount)::NUMERIC, 2) AS total_tips,
    ROUND(AVG(t.tip_percentage)::NUMERIC, 2) AS avg_tip_percentage,
    ROUND(AVG(t.fare_amount)::NUMERIC, 2) AS avg_fare_amount
FROM {{ ref('fact_trips') }} t
JOIN {{ ref('stg_trips') }} s ON t.trip_id = s.trip_id
LEFT JOIN {{ ref('dim_location') }} l on t.pickup_location_id = l.location_id
GROUP BY 1, 2
ORDER BY total_revenue DESC