SELECT trip_id
FROM {{ ref('fact_trips') }}
WHERE {{ selected_months('source_month') }} AND (
    trip_duration_min IS NULL OR trip_duration_min <= 0
    OR trip_duration_min > {{ env_var('MAX_DURATION_MIN', '1440') | float }}
    OR speed_mph IS NULL OR speed_mph > {{ env_var('MAX_SPEED_MPH', '120') | float }}
    OR trip_distance IS NULL OR trip_distance <= 0
    OR fare_amount IS NULL OR fare_amount <= 0
    OR DATE_TRUNC('month', pickup_date)::DATE <> source_month
)
