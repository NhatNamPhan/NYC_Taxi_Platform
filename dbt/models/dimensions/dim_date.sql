-- One row per calendar date spanning all published facts.
WITH bounds AS (
    SELECT MIN(pickup_date) AS first_date, MAX(pickup_date) AS last_date
    FROM {{ ref('fact_trips') }}
)
SELECT
    d::DATE AS date_id,
    DATE_TRUNC('month', d)::DATE AS month_start,
    EXTRACT(YEAR FROM d)::INTEGER AS year,
    EXTRACT(MONTH FROM d)::INTEGER AS month,
    EXTRACT(DAY FROM d)::INTEGER AS day,
    EXTRACT(ISODOW FROM d)::INTEGER AS day_of_week,
    TO_CHAR(d, 'FMDay') AS day_name,
    EXTRACT(ISODOW FROM d) IN (6, 7) AS is_weekend
FROM bounds CROSS JOIN LATERAL GENERATE_SERIES(first_date, last_date, INTERVAL '1 day') AS dates(d)
