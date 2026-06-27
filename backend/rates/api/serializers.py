"""DRF serializers — API shapes backed by dbt mart models."""

from rest_framework import serializers

from rates.models import MartLatestRate, MartRate, RawResponse

LATEST_RATE_FIELDS = [
    "provider",
    "rate_type",
    "rate_value",
    "effective_date",
    "ingestion_ts",
    "currency",
]


class RateSerializer(serializers.ModelSerializer):
    """Full rate row — includes database id (history + ingested paginated responses)."""

    provider = serializers.CharField(source="provider_name", read_only=True)

    class Meta:
        model = MartRate
        fields = ["id", *LATEST_RATE_FIELDS]


class LatestRateSerializer(serializers.ModelSerializer):
    """Latest-rate shape — one row per provider/type from mart_latest_rates."""

    provider = serializers.CharField(source="provider_name", read_only=True)

    class Meta:
        model = MartLatestRate
        fields = LATEST_RATE_FIELDS


class RawResponseSerializer(serializers.ModelSerializer):
    """Webhook ingest ack — raw payload stored; marts refresh via dbt."""

    class Meta:
        model = RawResponse
        fields = ["external_id", "parse_status", "fetched_at", "source_url"]


class IngestRateSerializer(serializers.Serializer):
    """Validates webhook payloads before parser.ingest_from_api_payload()."""

    provider = serializers.CharField(max_length=128)
    rate_type = serializers.CharField(max_length=64)
    rate_value = serializers.DecimalField(max_digits=8, decimal_places=4)
    effective_date = serializers.DateField()
    ingestion_ts = serializers.DateTimeField(required=False)
    currency = serializers.CharField(max_length=3, default="USD")
    source_url = serializers.URLField(required=False, allow_blank=True)
    raw_response_id = serializers.CharField(max_length=64, required=False)

    def validate_rate_value(self, value):
        if value <= 0:
            raise serializers.ValidationError("rate_value must be greater than zero.")
        return value
