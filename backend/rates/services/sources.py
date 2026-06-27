"""Strategy pattern — pluggable rate record sources (parquet, HTTP URL, future CSV)."""

import logging
from typing import Any, Iterator, Protocol

import pyarrow.parquet as pq

from rates.services.exceptions import InvalidIngestPayloadError
from rates.services.parser import parse_scrape_payload
from rates.services.scraper import fetch_rate_source

logger = logging.getLogger("rates.sources")

BATCH_SIZE = 10000


class RateRecordSource(Protocol):
    """Strategy interface — iterate rate records from any source (OCP)."""

    def iter_batches(self) -> Iterator[list[dict[str, Any]]]:
        ...


class ParquetRateSource:
    """Concrete strategy — streams Snappy-compressed parquet batches (no Python dedupe)."""

    def __init__(self, path: str, batch_size: int = BATCH_SIZE):
        self.path = path
        self.batch_size = batch_size

    def iter_batches(self) -> Iterator[list[dict[str, Any]]]:
        parquet_file = pq.ParquetFile(self.path)
        for batch in parquet_file.iter_batches(batch_size=self.batch_size):
            df = batch.to_pandas()
            yield df.to_dict(orient="records")


class HttpRateSource:
    """Concrete strategy — fetch a single JSON rate payload from a live URL."""

    def __init__(self, url: str):
        self.url = url

    def iter_batches(self) -> Iterator[list[dict[str, Any]]]:
        response = fetch_rate_source(self.url)
        parsed = parse_scrape_payload(response)
        if not parsed:
            logger.error(
                "HTTP scrape payload could not be parsed into a rate record",
                extra={
                    "event": "http_parse_failed",
                    "url": self.url,
                    "status_code": response.get("status_code"),
                },
            )
            raise InvalidIngestPayloadError(
                f"Could not parse rate record from HTTP response at {self.url}"
            )
        record = parsed.to_source_dict()
        if not record.get("source_url"):
            record["source_url"] = self.url
        yield [record]


def create_rate_source(path: str) -> RateRecordSource:
    """Factory Method — select concrete source implementation from path or URL."""
    if path.endswith(".parquet"):
        return ParquetRateSource(path)
    if path.startswith(("http://", "https://")):
        return HttpRateSource(path)
    raise ValueError(f"Unsupported rate source: {path}")
