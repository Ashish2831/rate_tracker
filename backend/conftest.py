"""Pytest defaults — test env vars for local runs without Docker."""

import os

os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret-key")
os.environ.setdefault("POSTGRES_DB", "rate_tracker_test")
os.environ.setdefault("POSTGRES_USER", "rate_tracker")
os.environ.setdefault("POSTGRES_PASSWORD", "rate_tracker")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("INGEST_BEARER_TOKEN", "test-bearer-token")
