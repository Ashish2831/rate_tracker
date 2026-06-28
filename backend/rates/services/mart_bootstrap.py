"""Helpers for detecting whether dbt analytics marts exist in Postgres."""

from django.db import connection


def marts_exist() -> bool:
    """True when dbt has created analytics.mart_latest_rates (API read path)."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT to_regclass('analytics.mart_latest_rates') IS NOT NULL")
        return bool(cursor.fetchone()[0])
