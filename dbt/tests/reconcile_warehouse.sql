-- Missing requested months fail, even if an old warehouse happens to exist.
{% set bounds = month_bounds() %}
WITH requested AS (
    SELECT d::DATE AS source_month
    FROM GENERATE_SERIES(DATE '{{ bounds.start }}', DATE '{{ bounds.end }}' - INTERVAL '1 month', INTERVAL '1 month') AS months(d)
), actual AS (
    SELECT source_month, COUNT(*) AS row_count
    FROM {{ ref('fact_trips') }} WHERE {{ selected_months('source_month') }} GROUP BY 1
)
SELECT r.source_month
FROM requested r
LEFT JOIN {{ source('gold', 'load_manifest') }} m USING (source_month)
LEFT JOIN actual a USING (source_month)
WHERE m.source_month IS NULL OR a.source_month IS NULL OR m.row_count <> a.row_count
