-- Classify both endpoints; tariff codes remain an additional signal.
SELECT t.source_month AS month_start,
    CASE
        WHEN 1 IN (t.pickup_location_id, t.dropoff_location_id) OR t.ratecode_id = 3 THEN 'Newark Airport'
        WHEN 132 IN (t.pickup_location_id, t.dropoff_location_id) OR t.ratecode_id = 2 THEN 'JFK Airport'
        WHEN 138 IN (t.pickup_location_id, t.dropoff_location_id) THEN 'LaGuardia Airport'
        ELSE 'City Trip'
    END AS trip_type,
    l.borough AS pickup_borough, {{ trip_metrics() }}
FROM {{ ref('fact_trips') }} t
LEFT JOIN {{ ref('dim_location') }} l ON t.pickup_location_id = l.location_id
WHERE {{ fact_month_filter() }}
GROUP BY 1, 2, 3
