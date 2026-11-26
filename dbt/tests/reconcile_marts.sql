WITH expected AS (
    SELECT source_month, COUNT(*) AS trip_count, SUM(total_amount) AS total_revenue
    FROM {{ ref('fact_trips') }} WHERE {{ selected_months('source_month') }} GROUP BY 1
), actual AS (
    {% for model in ['mart_kpi_summary', 'mart_monthly_trends', 'mart_hourly_demand', 'mart_day_of_week', 'mart_revenue_by_zone', 'mart_route_analysis', 'mart_airport_vs_city', 'mart_payment_insights'] %}
    SELECT '{{ model }}' AS model, month_start AS source_month,
        SUM(trip_count) AS trip_count, SUM(total_revenue) AS total_revenue
    FROM {{ ref(model) }} WHERE {{ selected_months('month_start') }} GROUP BY 1, 2
    {% if not loop.last %}UNION ALL{% endif %}
    {% endfor %}
), models AS (
    SELECT UNNEST(ARRAY['mart_kpi_summary', 'mart_monthly_trends', 'mart_hourly_demand', 'mart_day_of_week', 'mart_revenue_by_zone', 'mart_route_analysis', 'mart_airport_vs_city', 'mart_payment_insights']) AS model
)
SELECT m.model, e.source_month
FROM expected e CROSS JOIN models m
LEFT JOIN actual a ON e.source_month = a.source_month AND m.model = a.model
WHERE a.source_month IS NULL OR a.trip_count <> e.trip_count OR a.total_revenue <> e.total_revenue
