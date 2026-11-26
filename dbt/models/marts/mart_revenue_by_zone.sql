SELECT t.source_month AS month_start,
    l.location_id AS pickup_location_id, l.zone AS pickup_zone, l.borough AS pickup_borough,
    {{ trip_metrics() }}
FROM {{ ref('fact_trips') }} t
LEFT JOIN {{ ref('dim_location') }} l ON t.pickup_location_id = l.location_id
WHERE {{ fact_month_filter() }}
GROUP BY 1, 2, 3, 4
