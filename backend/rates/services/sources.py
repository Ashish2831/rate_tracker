"""Strategy pattern — pluggable rate record sources (parquet, HTTP URL, future CSV)."""

from typing import Any, Iterator, Protocol

import pyarrow.parquet as pq

from rates.services.parser import parse_scrape_payload
from rates.services.scraper import fetch_rate_source

BATCH_SIZE = 10000


class RateRecordSource(Protocol):
    """Strategy interface — iterate rate records from any source (OCP)."""

    def iter_batches(self) -> Iterator[list[dict[str, Any]]]:
        ...


class ParquetRateSource:
    """Concrete strategy — reads Snappy-compressed parquet in deduplicated batches."""

    def __init__(self, path: str, batch_size: int = BATCH_SIZE):
        self.path = path
        self.batch_size = batch_size

    def iter_batches(self) -> Iterator[list[dict[str, Any]]]:
        parquet_file = pq.ParquetFile(self.path)
        for batch in parquet_file.iter_batches(batch_size=self.batch_size):
            df = batch.to_pandas()
            # ~97% of seed rows share a business key; keep the latest observation.
            # Sort the dataframe by ingestion timestamp and drop duplicates based on provider, rate type, and effective date
            df = df.sort_values("ingestion_ts").drop_duplicates(
                subset=["provider", "rate_type", "effective_date"],
                keep="last",
            )
            yield df.to_dict(orient="records") # Convert the dataframe to a list of dictionaries


class HttpRateSource:
    """Concrete strategy — fetch a single JSON rate payload from a live URL."""

    def __init__(self, url: str):
        self.url = url

    def iter_batches(self) -> Iterator[list[dict[str, Any]]]:
        response = fetch_rate_source(self.url)
        parsed = parse_scrape_payload(response)
        if not parsed:
            return
        yield [
            {
                "provider": parsed.provider_name,
                "rate_type": parsed.rate_type,
                "rate_value": parsed.rate_value,
                "effective_date": parsed.effective_date,
                "ingestion_ts": parsed.ingestion_ts,
                "currency": parsed.currency,
                "source_url": parsed.source_url or self.url,
                "raw_response_id": parsed.external_id,
            }
        ]


def create_rate_source(path: str) -> RateRecordSource:
    """Factory Method — select concrete source implementation from path or URL."""
    if path.endswith(".parquet"):
        return ParquetRateSource(path)
    if path.startswith(("http://", "https://")):
        return HttpRateSource(path)
    raise ValueError(f"Unsupported rate source: {path}")
