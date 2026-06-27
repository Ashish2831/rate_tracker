"""Value object — typed representation of a normalized rate record after parsing."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any


@dataclass
class ParsedRate:
    """Normalized record flowing from parser → RateWriter (webhook path)."""

    external_id: str  # Maps to RawResponse.external_id for idempotent ingest
    provider_name: str
    rate_type: str
    rate_value: Decimal | None  # None → partial record (excluded from read APIs)
    effective_date: date | str
    ingestion_ts: datetime | str
    currency: str
    source_url: str
    raw_body: dict[str, Any]
    parse_status: str  # success | partial | failed
    error_message: str

    @property
    def is_failed(self) -> bool:
        return self.parse_status == "failed"

    def to_source_dict(self) -> dict[str, Any]:
        """Shape expected by bulk raw ingest (HTTP adapter → ParquetRateSource path)."""
        return {
            "provider": self.provider_name,
            "rate_type": self.rate_type,
            "rate_value": self.rate_value,
            "effective_date": self.effective_date,
            "ingestion_ts": self.ingestion_ts,
            "currency": self.currency,
            "source_url": self.source_url,
            "raw_response_id": self.external_id,
        }
