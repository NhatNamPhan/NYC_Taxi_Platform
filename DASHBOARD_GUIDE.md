# Superset dashboard guide

The eight dbt marts are in the `mart` schema. `bi_reader` has SELECT access to this schema only. Provision the database, datasets and three dashboards after `dbt build`:

```powershell
docker compose --env-file .env.compose --profile tools run --rm superset-assets
```

## Dashboard pages

| Slug | Purpose | Main datasets |
|---|---|---|
| `nyc-overview` | Revenue, trips, average fare, recorded card tips, monthly trends | `mart_kpi_summary`, `mart_monthly_trends` |
| `nyc-demand` | Hourly demand, top pickup zones, day of week | `mart_hourly_demand`, `mart_revenue_by_zone`, `mart_day_of_week` |
| `nyc-routes` | Top routes, airport segments, payment methods | `mart_route_analysis`, `mart_airport_vs_city`, `mart_payment_insights` |

## Filter grain

All marts retain `month_start` as a DATE. The dashboard month-range control uses this temporal column across charts. Choose boundaries on the first of a month; the upper boundary is exclusive. To compare January and February 2025, choose `2025-01-01 <= month_start < 2025-03-01`.

These are **monthly-grain marts**, so partial-day/date filtering is not supported. Borough is present where appropriate; `mart_monthly_trends` and `mart_day_of_week` are city-wide. Do not apply a borough filter to a city-wide dataset and assume it changes the result.

## Aggregations across months

| Display | SQL metric |
|---|---|
| Trips | `SUM(trip_count)` |
| Recorded revenue | `SUM(total_revenue)` |
| Average base fare | `SUM(total_fare) / NULLIF(SUM(trip_count), 0)` |
| Average distance | `SUM(total_distance) / NULLIF(SUM(trip_count), 0)` |
| Average duration | `SUM(total_duration_min) / NULLIF(SUM(trip_count), 0)` |
| Effective aggregate speed | `60 * SUM(total_distance) / NULLIF(SUM(total_duration_min), 0)` |
| Recorded credit-card tip percentage | `100 * SUM(card_tips) / NULLIF(SUM(card_fare), 0)` |

Use these additive components rather than averaging monthly averages. Precomputed `avg_*` columns are convenient for an individual mart row; use the formulas above after regrouping/filtering.

`total_revenue` means TLC's recorded `total_amount` for the accepted analytical population. It includes fees and recorded tips; it is not profit or a complete ledger of refunds/voids. Cash tips are absent from the source. Speed is distance divided by duration, not a measurement of road traffic.

## Airport categories

Airport classification checks pickup **and** dropoff location: Newark=1, JFK=132, LaGuardia=138. JFK/Newark rate codes are additional signals. A trip touching multiple airports is assigned one category using priority Newark, JFK, then LaGuardia. Nassau/Westchester is not treated as an airport by itself.

## Freshness and evidence

`mart_kpi_summary.data_updated_at` comes from the committed warehouse manifest. Compare it to the latest successful Airflow/dbt run. The quality JSON and quarantine record exclusions; compare totals using the same selected source months and cleaning policy.

Dashboard provisioning is idempotent but owns the managed chart names/slugs and layouts. Duplicate assets before making independent UI edits. No benchmark latency or business conclusion is claimed without measurement on the actual data.
