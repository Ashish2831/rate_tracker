"""Test helpers — create dbt mart tables and seed rows without running full dbt."""

from datetime import date
from decimal import Decimal

from django.db import connection
from django.utils import timezone


MART_DDL = """
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE TABLE IF NOT EXISTS analytics.mart_rates (
    id BIGINT PRIMARY KEY,
    provider_name VARCHAR(128) NOT NULL,
    normalized_name VARCHAR(128) NOT NULL,
    rate_type VARCHAR(64) NOT NULL,
    rate_value NUMERIC(8, 4) NOT NULL,
    effective_date DATE NOT NULL,
    ingestion_ts TIMESTAMPTZ NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    external_id VARCHAR(64) NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS analytics.mart_latest_rates (
    id BIGINT PRIMARY KEY,
    provider_name VARCHAR(128) NOT NULL,
    normalized_name VARCHAR(128) NOT NULL,
    rate_type VARCHAR(64) NOT NULL,
    rate_value NUMERIC(8, 4) NOT NULL,
    effective_date DATE NOT NULL,
    ingestion_ts TIMESTAMPTZ NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    external_id VARCHAR(64) NOT NULL UNIQUE
);
"""


def ensure_mart_tables() -> None:
    with connection.cursor() as cursor:
        cursor.execute(MART_DDL)


def insert_sample_mart_rate(
    *,
    provider_name: str = "Chase",
    normalized_name: str = "chase",
    rate_type: str = "30yr_fixed_mortgage",
    rate_value: Decimal = Decimal("6.5000"),
    effective_date: date | None = None,
    external_id: str = "mart-test-001",
    row_id: int = 1,
) -> None:
    """Insert matching rows into mart_rates and mart_latest_rates for API tests."""
    ensure_mart_tables()
    effective = effective_date or date.today()
    ingested = timezone.now()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO analytics.mart_rates (
                id, provider_name, normalized_name, rate_type, rate_value,
                effective_date, ingestion_ts, currency, external_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (external_id) DO NOTHING
            """,
            [
                row_id,
                provider_name,
                normalized_name,
                rate_type,
                rate_value,
                effective,
                ingested,
                "USD",
                external_id,
            ],
        )
        cursor.execute(
            """
            INSERT INTO analytics.mart_latest_rates (
                id, provider_name, normalized_name, rate_type, rate_value,
                effective_date, ingestion_ts, currency, external_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (external_id) DO NOTHING
            """,
            [
                row_id,
                provider_name,
                normalized_name,
                rate_type,
                rate_value,
                effective,
                ingested,
                "USD",
                external_id,
            ],
        )
