SELECT t.source_month AS month_start,
    d.day_of_week, d.day_name, d.is_weekend,
    CASE WHEN d.is_weekend THEN 'Weekend' ELSE 'Weekday' END AS day_type,
    {{ trip_metrics() }}
FROM {{ ref('fact_trips') }} t
JOIN {{ ref('dim_date') }} d ON t.pickup_date = d.date_id
WHERE {{ fact_month_filter() }}
GROUP BY 1, 2, 3, 4, 5
