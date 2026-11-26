SELECT t.source_month AS month_start, t.pickup_hour,
    l.borough AS pickup_borough, {{ trip_metrics() }}
FROM {{ ref('fact_trips') }} t
LEFT JOIN {{ ref('dim_location') }} l ON t.pickup_location_id = l.location_id
WHERE {{ fact_month_filter() }}
GROUP BY 1, 2, 3
