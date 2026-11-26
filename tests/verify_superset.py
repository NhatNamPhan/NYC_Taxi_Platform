"""Check provisioned chart queries and month filters via the local Superset API.

Run inside the Superset container after provisioning synthetic validation assets:
  python /app/verify_superset.py
This does not claim screenshot/visual QA; it verifies server-side chart queries.
"""
import json
import os
import requests
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.exc import DBAPIError


def main():
    session = requests.Session()
    base = os.getenv("SUPERSET_TEST_URL", "http://superset:8088")
    result = session.post(base + "/api/v1/security/login", json={
        "username": os.getenv("SUPERSET_ADMIN_USERNAME", "admin"),
        "password": os.environ["SUPERSET_ADMIN_PASSWORD"], "provider": "db", "refresh": True,
    }, timeout=30)
    result.raise_for_status()
    session.headers["Authorization"] = f"Bearer {result.json()['access_token']}"
    csrf = session.get(base + "/api/v1/security/csrf_token/", timeout=30)
    csrf.raise_for_status()
    session.headers["X-CSRFToken"] = csrf.json()["result"]
    response = session.get(base + "/api/v1/dashboard/", params={"q": "(page_size:100)"}, timeout=30)
    response.raise_for_status()
    dashboards = [d for d in response.json()["result"] if d.get("slug", "").startswith("validation-")]
    assert len(dashboards) == 3, dashboards
    response = session.get(base + "/api/v1/chart/", params={"q": "(page_size:100)"}, timeout=30)
    response.raise_for_status()
    charts = [c for c in response.json()["result"] if c["slice_name"].startswith("validation-")]
    assert len(charts) == 12, len(charts)
    for chart in charts:
        detail = session.get(base + f"/api/v1/chart/{chart['id']}", timeout=30)
        detail.raise_for_status()
        cfg = json.loads(detail.json()["result"]["params"])
        columns = list(cfg.get("groupby", []))
        timeseries = cfg.get("x_axis") == "month_start"
        if cfg.get("x_axis") and not timeseries:
            columns.insert(0, cfg["x_axis"])
        query = {"columns": columns, "metrics": cfg.get("metrics", [cfg.get("metric")]),
                 "is_timeseries": timeseries, "granularity": "month_start", "row_limit": 100,
                 "time_range": "No filter", "extras": {"time_grain_sqla": "P1M"}}
        payload = {"datasource": {"id": int(cfg["datasource"].split("__")[0]), "type": "table"},
                   "force": True, "queries": [query], "result_format": "json", "result_type": "full"}
        data = session.post(base + "/api/v1/chart/data", json=payload, timeout=30)
        assert data.ok, (chart["slice_name"], data.text)
        assert data.json()["result"][0]["status"] == "success", data.text
        assert data.json()["result"][0]["data"], chart["slice_name"]
        if chart["slice_name"] == "validation-overview: Total revenue":
            all_months = data.json()["result"][0]["data"][0]["Revenue"]
            query["time_range"] = "2025-01-01 : 2025-02-01"
            january = session.post(base + "/api/v1/chart/data", json=payload, timeout=30)
            assert january.ok, january.text
            jan_revenue = january.json()["result"][0]["data"][0]["Revenue"]
            assert all_months == 67 and jan_revenue == 19, (all_months, jan_revenue)
        print("PASS chart:", chart["slice_name"])
    engine = create_engine(URL.create("postgresql+psycopg2", username="bi_reader",
                                     password=os.environ["BI_READER_PASSWORD"], host="postgres",
                                     database="nyc_taxi_test"))
    for statement in ["SELECT * FROM core.fact_trips LIMIT 1", "DELETE FROM mart.mart_kpi_summary WHERE FALSE"]:
        try:
            with engine.begin() as conn:
                conn.execute(text(statement))
        except DBAPIError as error:
            assert "permission denied" in str(error).lower(), str(error)
        else:
            raise AssertionError("BI role unexpectedly accessed core data or wrote a mart")
    print("PASS: 3 dashboards, 12 chart queries, January filter and read-only mart access")


if __name__ == "__main__":
    main()
