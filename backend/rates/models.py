"""Django ORM models — raw ingest (bronze) and dbt mart mirrors (read-only)."""

import uuid

from django.db import models


class RawResponse(models.Model):
    """Immutable scrape payload; external_id enforces idempotent re-ingestion."""

    class ParseStatus(models.TextChoices):
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        PARTIAL = "partial", "Partial"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    external_id = models.CharField(max_length=64, unique=True, db_index=True)
    source_url = models.URLField(max_length=512)
    raw_body = models.JSONField()
    fetched_at = models.DateTimeField(db_index=True)
    parse_status = models.CharField(
        max_length=16, choices=ParseStatus.choices, default=ParseStatus.SUCCESS
    )
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["fetched_at"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.external_id} ({self.parse_status})"


class MartRate(models.Model):
    """dbt analytics.mart_rates — cleaned, deduplicated rate facts (Option B read path)."""

    id = models.BigIntegerField(primary_key=True)
    provider_name = models.CharField(max_length=128)
    normalized_name = models.CharField(max_length=128, db_index=True)
    rate_type = models.CharField(max_length=64, db_index=True)
    rate_value = models.DecimalField(max_digits=8, decimal_places=4)
    effective_date = models.DateField(db_index=True)
    ingestion_ts = models.DateTimeField(db_index=True)
    currency = models.CharField(max_length=3, default="USD")
    external_id = models.CharField(max_length=64, unique=True)

    class Meta:
        managed = False
        db_table = '"analytics"."mart_rates"'
        ordering = ["-effective_date", "-ingestion_ts"]

    def __str__(self) -> str:
        return f"{self.provider_name} {self.rate_type} @ {self.effective_date}"


class MartLatestRate(models.Model):
    """dbt analytics.mart_latest_rates — one row per (provider, rate_type) for GET /latest."""

    id = models.BigIntegerField(primary_key=True)
    provider_name = models.CharField(max_length=128)
    normalized_name = models.CharField(max_length=128, db_index=True)
    rate_type = models.CharField(max_length=64, db_index=True)
    rate_value = models.DecimalField(max_digits=8, decimal_places=4)
    effective_date = models.DateField()
    ingestion_ts = models.DateTimeField()
    currency = models.CharField(max_length=3, default="USD")
    external_id = models.CharField(max_length=64, unique=True)

    class Meta:
        managed = False
        db_table = '"analytics"."mart_latest_rates"'
        ordering = ["provider_name", "rate_type"]

    def __str__(self) -> str:
        return f"{self.provider_name} {self.rate_type} = {self.rate_value}"
