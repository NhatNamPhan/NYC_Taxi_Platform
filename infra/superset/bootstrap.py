"""Provision three editable dashboards after dbt build; reruns update managed assets."""
import json
import os
from sqlalchemy import inspect
from sqlalchemy.engine import URL
from superset.app import create_app


def metric(label, expression):
    return {"expressionType": "SQL", "sqlExpression": expression, "label": label,
            "hasCustomLabel": True, "optionName": f"metric_{label.lower().replace(' ', '_')}"}


REVENUE = metric("Revenue", "SUM(total_revenue)")
TRIPS = metric("Trips", "SUM(trip_count)")
AVG_FARE = metric("Average fare", "SUM(total_fare) / NULLIF(SUM(trip_count), 0)")
CARD_TIP = metric("Card tip percent", "100.0 * SUM(card_tips) / NULLIF(SUM(card_fare), 0)")

PAGES = [
    ("nyc-overview", "NYC Taxi | Revenue overview", [
        ("Total revenue", "mart_kpi_summary", "big_number_total", {"metric": REVENUE, "y_axis_format": "$,.0f"}),
        ("Total trips", "mart_kpi_summary", "big_number_total", {"metric": TRIPS, "y_axis_format": ",.0f"}),
        ("Average fare", "mart_kpi_summary", "big_number_total", {"metric": AVG_FARE, "y_axis_format": "$,.2f"}),
        ("Recorded card tip %", "mart_kpi_summary", "big_number_total", {"metric": CARD_TIP, "y_axis_format": ".2f"}),
        ("Monthly revenue", "mart_monthly_trends", "echarts_timeseries_line",
         {"x_axis": "month_start", "time_grain_sqla": "P1M", "metrics": [REVENUE], "groupby": [], "y_axis_format": "$,.0f"}),
        ("Revenue by pickup borough", "mart_kpi_summary", "table",
         {"query_mode": "aggregate", "groupby": ["pickup_borough"], "metrics": [REVENUE, TRIPS, AVG_FARE], "order_desc": True}),
    ]),
    ("nyc-demand", "NYC Taxi | Demand and locations", [
        ("Trips by pickup hour", "mart_hourly_demand", "echarts_timeseries_bar",
         {"x_axis": "pickup_hour", "metrics": [TRIPS], "groupby": ["pickup_borough"], "stack": "Stack", "x_axis_sort_asc": True}),
        ("Top 10 pickup zones", "mart_revenue_by_zone", "table",
         {"query_mode": "aggregate", "groupby": ["pickup_zone", "pickup_borough"], "metrics": [REVENUE, TRIPS], "row_limit": 10, "order_desc": True}),
        ("Day of week", "mart_day_of_week", "table",
         {"query_mode": "aggregate", "groupby": ["day_of_week", "day_name", "day_type"], "metrics": [TRIPS, REVENUE]}),
    ]),
    ("nyc-routes", "NYC Taxi | Routes and payments", [
        ("Top 20 routes", "mart_route_analysis", "table",
         {"query_mode": "aggregate", "groupby": ["route_name"], "metrics": [TRIPS, REVENUE,
          metric("Effective speed mph", "60.0 * SUM(total_distance) / NULLIF(SUM(total_duration_min), 0)")], "row_limit": 20, "order_desc": True}),
        ("Airport versus city", "mart_airport_vs_city", "table",
         {"query_mode": "aggregate", "groupby": ["trip_type"], "metrics": [REVENUE, TRIPS, AVG_FARE]}),
        ("Payment methods", "mart_payment_insights", "table",
         {"query_mode": "aggregate", "groupby": ["payment_method"], "metrics": [REVENUE, TRIPS, CARD_TIP]}),
    ]),
]


def main():
    app = create_app()
    with app.app_context():
        from superset import db, security_manager
        from superset.models.core import Database
        from superset.models.dashboard import Dashboard
        from superset.models.slice import Slice
        from superset.connectors.sqla.models import SqlaTable

        data_db = os.getenv("BI_DATABASE_NAME", "nyc_taxi")
        prefix = os.getenv("SUPERSET_ASSET_PREFIX", "nyc")
        database_name = "NYC Taxi Marts" if data_db == "nyc_taxi" else "NYC Taxi Validation (synthetic)"
        uri = URL.create("postgresql+psycopg2", username="bi_reader", password=os.environ["BI_READER_PASSWORD"],
                         host="postgres", port=5432, database=data_db).render_as_string(hide_password=False)
        database = db.session.query(Database).filter_by(database_name=database_name).one_or_none()
        if database is None:
            database = Database(database_name=database_name)
            db.session.add(database)
        database.sqlalchemy_uri = uri
        database.expose_in_sqllab = True
        database.allow_ctas = False
        database.allow_cvas = False
        database.allow_dml = False
        db.session.flush()
        required = {chart[1] for _, _, charts in PAGES for chart in charts}
        with database.get_sqla_engine() as engine:
            existing = set(inspect(engine).get_table_names(schema="mart"))
        missing = required - existing
        if missing:
            raise RuntimeError(f"Run dbt build successfully before provisioning dashboards. Missing marts: {sorted(missing)}")
        owner = security_manager.find_user(username=os.environ.get("SUPERSET_ADMIN_USERNAME", "admin"))
        datasets = {}
        for name in sorted(required):
            dataset = db.session.query(SqlaTable).filter_by(database_id=database.id, schema="mart", table_name=name).one_or_none()
            if dataset is None:
                dataset = SqlaTable(table_name=name, schema="mart", database=database, owners=[owner])
                db.session.add(dataset)
            db.session.flush()
            dataset.fetch_metadata()
            dataset.main_dttm_col = "month_start"
            datasets[name] = dataset
        db.session.flush()
        for slug, title, definitions in PAGES:
            slug = slug.replace("nyc-", f"{prefix}-", 1)
            if data_db != "nyc_taxi":
                title = f"Synthetic demo | {title}"
            dashboard = db.session.query(Dashboard).filter_by(slug=slug).one_or_none()
            if dashboard is None:
                dashboard = Dashboard(slug=slug, owners=[owner])
                db.session.add(dashboard)
            dashboard.dashboard_title = title
            dashboard.published = True
            slices = []
            for name, table, viz, settings in definitions:
                dataset = datasets[table]
                chart_name = f"{slug}: {name}"
                chart = db.session.query(Slice).filter_by(slice_name=chart_name).one_or_none()
                if chart is None:
                    chart = Slice(slice_name=chart_name, owners=[owner])
                    db.session.add(chart)
                chart.datasource_id = dataset.id
                chart.datasource_type = "table"
                chart.viz_type = viz
                chart.params = json.dumps({"viz_type": viz, "datasource": f"{dataset.id}__table",
                                           "granularity_sqla": "month_start", "time_range": "No filter",
                                           "adhoc_filters": [], "row_limit": 1000, **settings})
                slices.append(chart)
            db.session.flush()
            dashboard.slices = slices
            position = {
                "DASHBOARD_VERSION_KEY": "v2",
                "ROOT_ID": {"id": "ROOT_ID", "type": "ROOT", "children": ["GRID_ID"]},
                "GRID_ID": {"id": "GRID_ID", "type": "GRID", "children": [], "parents": ["ROOT_ID"]},
            }
            used_width, row_number = 12, -1
            for chart in slices:
                width = 3 if chart.viz_type == "big_number_total" else 6
                if used_width + width > 12:
                    row_number += 1
                    used_width = 0
                    row_id = f"ROW-{row_number}"
                    position["GRID_ID"]["children"].append(row_id)
                    position[row_id] = {"id": row_id, "type": "ROW", "children": [], "parents": ["ROOT_ID", "GRID_ID"], "meta": {"background": "BACKGROUND_TRANSPARENT"}}
                chart_id = f"CHART-{chart.id}"
                position[row_id]["children"].append(chart_id)
                used_width += width
                position[chart_id] = {"id": chart_id, "type": "CHART", "children": [], "parents": ["ROOT_ID", "GRID_ID", row_id],
                                      "meta": {"chartId": chart.id, "width": width, "height": 14 if width == 3 else 45, "sliceName": chart.slice_name}}
            dashboard.position_json = json.dumps(position)
            dashboard.json_metadata = json.dumps({"native_filter_configuration": [{
                "id": f"NATIVE_FILTER-{slug}-month", "name": "Month range", "filterType": "filter_time",
                "targets": [{}], "controlValues": {}, "cascadeParentIds": [],
                "defaultDataMask": {"extraFormData": {"time_range": "No filter"}, "filterState": {"value": "No filter"}},
                "scope": {"rootPath": ["ROOT_ID"], "excluded": []}, "type": "NATIVE_FILTER",
            }]})
            print(f"Provisioned /superset/dashboard/{slug}/")
        db.session.commit()


if __name__ == "__main__":
    main()
