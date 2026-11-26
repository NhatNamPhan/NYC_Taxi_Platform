SELECT t.source_month AS month_start, l.borough AS pickup_borough,
    {{ trip_metrics() }}, MAX(m.loaded_at) AS data_updated_at
FROM {{ ref('fact_trips') }} t
LEFT JOIN {{ ref('dim_location') }} l ON t.pickup_location_id = l.location_id
JOIN {{ source('gold', 'load_manifest') }} m ON t.source_month = m.source_month
WHERE {{ fact_month_filter() }}
GROUP BY 1, 2
