"""Value object — typed representation of a normalized rate record after parsing."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any


@dataclass
class ParsedRate:
    external_id: str
    provider_name: str
    rate_type: str
    rate_value: Decimal | None
    effective_date: date | str
    ingestion_ts: datetime | str
    currency: str
    source_url: str
    raw_body: dict[str, Any]
    parse_status: str
    error_message: str

    @property
    def is_partial(self) -> bool:
        return self.parse_status == "partial"
