"""DRF serializers — shared field lists for latest and history responses."""

from rest_framework import serializers

from rates.models import Rate

# Single source of truth for latest-rate JSON shape across serializers.
LATEST_RATE_FIELDS = [
    "provider",
    "rate_type",
    "rate_value",
    "effective_date",
    "ingestion_ts",
    "currency",
]


class RateSerializer(serializers.ModelSerializer):
    provider = serializers.CharField(source="provider.name", read_only=True)

    class Meta:
        model = Rate
        fields = ["id", *LATEST_RATE_FIELDS]


class LatestRateSerializer(serializers.ModelSerializer):
    provider = serializers.CharField(source="provider.name", read_only=True)

    class Meta:
        model = Rate
        fields = LATEST_RATE_FIELDS


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
