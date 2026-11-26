{% macro generate_schema_name(custom_schema_name, node) -%}
    {{ custom_schema_name | trim if custom_schema_name else target.schema }}
{%- endmacro %}

{% macro month_bounds() %}
    {% set start = env_var('PIPELINE_START_MONTH', '2025-01') %}
    {% set end = env_var('PIPELINE_END_MONTH', '2025-01') %}
    {% set first = modules.datetime.datetime.strptime(start, '%Y-%m') %}
    {% set last = modules.datetime.datetime.strptime(end, '%Y-%m') %}
    {% if first > last %}{{ exceptions.raise_compiler_error('Start month is after end month') }}{% endif %}
    {% set following = (last.replace(day=28) + modules.datetime.timedelta(days=4)).replace(day=1) %}
    {{ return({'start': first.strftime('%Y-%m-%d'), 'end': following.strftime('%Y-%m-%d')}) }}
{% endmacro %}

{% macro selected_months(column) %}
    {% set bounds = month_bounds() %}
    {{ column }} >= DATE '{{ bounds.start }}' AND {{ column }} < DATE '{{ bounds.end }}'
{% endmacro %}

{% macro delete_selected_months(column) %}
    {% if is_incremental() %}
        DELETE FROM {{ this }} WHERE {{ selected_months(column) }}
    {% else %}
        SELECT 1
    {% endif %}
{% endmacro %}

{% macro fact_month_filter(column='t.source_month') %}
    {% if is_incremental() %}{{ selected_months(column) }}{% else %}TRUE{% endif %}
{% endmacro %}

{% macro trip_metrics(t='t') %}
    COUNT(*) AS trip_count,
    SUM({{ t }}.total_amount) AS total_revenue,
    SUM({{ t }}.fare_amount) AS total_fare,
    SUM({{ t }}.tip_amount) AS total_tips,
    SUM({{ t }}.airport_fee) AS total_airport_fees,
    SUM({{ t }}.cbd_congestion_fee) AS total_cbd_congestion_fee,
    SUM({{ t }}.trip_distance) AS total_distance,
    SUM({{ t }}.trip_duration_min) AS total_duration_min,
    SUM(CASE WHEN {{ t }}.payment_type = 1 THEN {{ t }}.tip_amount ELSE 0 END) AS card_tips,
    SUM(CASE WHEN {{ t }}.payment_type = 1 THEN {{ t }}.fare_amount ELSE 0 END) AS card_fare,
    ROUND(SUM({{ t }}.fare_amount) / NULLIF(COUNT(*), 0), 2) AS avg_fare_amount,
    ROUND((SUM({{ t }}.trip_distance) / NULLIF(COUNT(*), 0))::NUMERIC, 2) AS avg_trip_distance,
    ROUND((SUM({{ t }}.trip_duration_min) / NULLIF(COUNT(*), 0))::NUMERIC, 2) AS avg_duration_min,
    ROUND((60 * SUM({{ t }}.trip_distance) / NULLIF(SUM({{ t }}.trip_duration_min), 0))::NUMERIC, 2) AS avg_speed_mph,
    ROUND(100 * SUM(CASE WHEN {{ t }}.payment_type = 1 THEN {{ t }}.tip_amount ELSE 0 END)
        / NULLIF(SUM(CASE WHEN {{ t }}.payment_type = 1 THEN {{ t }}.fare_amount ELSE 0 END), 0), 2) AS card_tip_percentage
{% endmacro %}
