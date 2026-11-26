{{ config(indexes=[
    {'columns': ['source_month', 'trip_id'], 'unique': true},
    {'columns': ['pickup_date']},
    {'columns': ['pickup_location_id']},
    {'columns': ['dropoff_location_id']}
]) }}
SELECT *
FROM {{ ref('stg_trips') }} t
WHERE {{ fact_month_filter() }}
