"""Idempotently migrate Superset metadata and create the configured administrator."""
import os
import subprocess

subprocess.run(["superset", "db", "upgrade"], check=True)
subprocess.run(["superset", "init"], check=True)

from superset.app import create_app
from superset import db, security_manager

app = create_app()
with app.app_context():
    username = os.environ.get("SUPERSET_ADMIN_USERNAME", "admin")
    if security_manager.find_user(username=username) is None:
        user = security_manager.add_user(
            username=username, first_name="Platform", last_name="Admin", email="admin@example.local",
            role=security_manager.find_role("Admin"), password=os.environ["SUPERSET_ADMIN_PASSWORD"],
        )
        if not user:
            raise RuntimeError("Unable to create Superset administrator")
        db.session.commit()
