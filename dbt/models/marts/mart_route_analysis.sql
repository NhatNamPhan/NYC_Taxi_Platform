SELECT t.source_month AS month_start,
    t.pickup_location_id, t.dropoff_location_id,
    pu.borough AS pickup_borough, pu.zone AS pickup_zone,
    drp.borough AS dropoff_borough, drp.zone AS dropoff_zone,
    pu.zone || ' -> ' || drp.zone AS route_name,
    {{ trip_metrics() }}
FROM {{ ref('fact_trips') }} t
LEFT JOIN {{ ref('dim_location') }} pu ON t.pickup_location_id = pu.location_id
LEFT JOIN {{ ref('dim_location') }} drp ON t.dropoff_location_id = drp.location_id
WHERE {{ fact_month_filter() }}
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8
