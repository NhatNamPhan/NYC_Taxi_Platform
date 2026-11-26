SELECT
    t.source_month AS month_start,
    EXTRACT(YEAR FROM t.source_month)::INTEGER AS year,
    EXTRACT(MONTH FROM t.source_month)::INTEGER AS month,
    {{ trip_metrics() }}
FROM {{ ref('fact_trips') }} t
WHERE {{ fact_month_filter() }}
GROUP BY 1, 2, 3
