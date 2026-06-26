import uuid

from django.db import models


class Provider(models.Model):
    name = models.CharField(max_length=128, unique=True)
    normalized_name = models.CharField(max_length=128, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["normalized_name"]

    def __str__(self) -> str:
        return self.name


class RawResponse(models.Model):
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
        ]

    def __str__(self) -> str:
        return f"{self.external_id} ({self.parse_status})"


class Rate(models.Model):
    provider = models.ForeignKey(Provider, on_delete=models.PROTECT, related_name="rates")
    rate_type = models.CharField(max_length=64, db_index=True)
    rate_value = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    effective_date = models.DateField(db_index=True)
    ingestion_ts = models.DateTimeField(db_index=True)
    currency = models.CharField(max_length=3, default="USD")
    raw_response = models.ForeignKey(
        RawResponse, on_delete=models.PROTECT, related_name="rates", null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["provider", "rate_type", "-effective_date"]),
            models.Index(fields=["provider", "rate_type", "effective_date"]),
            models.Index(fields=["-ingestion_ts"]),
            models.Index(fields=["ingestion_ts"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "rate_type", "effective_date", "ingestion_ts"],
                name="unique_rate_snapshot",
            ),
        ]
        ordering = ["-effective_date", "-ingestion_ts"]

    def __str__(self) -> str:
        return f"{self.provider.name} {self.rate_type} @ {self.effective_date}"
