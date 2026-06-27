"""Pytest defaults — test env vars for local runs without Docker."""

import os
from pathlib import Path

os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret-key")
os.environ.setdefault("POSTGRES_DB", "rate_tracker_test")
os.environ.setdefault("POSTGRES_USER", "rate_tracker")
os.environ.setdefault("POSTGRES_PASSWORD", "rate_tracker")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("INGEST_BEARER_TOKEN", "test-bearer-token")
os.environ.setdefault("DBT_RUN_AFTER_INGEST", "false")
os.environ.setdefault("DBT_PROJECT_DIR", str(Path(__file__).resolve().parent.parent / "dbt"))
os.environ.setdefault("DBT_PROFILES_DIR", os.environ["DBT_PROJECT_DIR"])
