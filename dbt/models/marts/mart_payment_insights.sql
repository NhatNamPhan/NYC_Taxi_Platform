SELECT t.source_month AS month_start,
    CASE t.payment_type
        WHEN 0 THEN 'Flex Fare' WHEN 1 THEN 'Credit Card' WHEN 2 THEN 'Cash'
        WHEN 3 THEN 'No Charge' WHEN 4 THEN 'Dispute' WHEN 6 THEN 'Voided'
        ELSE 'Unknown'
    END AS payment_method,
    l.borough AS pickup_borough, {{ trip_metrics() }}
FROM {{ ref('fact_trips') }} t
LEFT JOIN {{ ref('dim_location') }} l ON t.pickup_location_id = l.location_id
WHERE {{ fact_month_filter() }}
GROUP BY 1, 2, 3
