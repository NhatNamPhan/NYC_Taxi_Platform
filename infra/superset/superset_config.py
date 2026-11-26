import os
from sqlalchemy.engine import URL

SECRET_KEY = os.environ["SUPERSET_SECRET_KEY"]
SQLALCHEMY_DATABASE_URI = URL.create(
    "postgresql+psycopg2", username="superset", password=os.environ["SUPERSET_DB_PASSWORD"],
    host="postgres", port=5432, database="superset",
).render_as_string(hide_password=False)
WTF_CSRF_ENABLED = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
TALISMAN_ENABLED = False  # Local HTTP demo, bound to loopback by Compose.
SQLLAB_TIMEOUT = 60
SUPERSET_WEBSERVER_TIMEOUT = 120
ROW_LIMIT = 10000
FEATURE_FLAGS = {"DASHBOARD_NATIVE_FILTERS": True}
