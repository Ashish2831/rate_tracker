"""Strategy pattern — pluggable rate record sources (parquet today; HTTP/CSV later)."""

from typing import Any, Iterator, Protocol

import pyarrow.parquet as pq

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
            df = df.sort_values("ingestion_ts").drop_duplicates(
                subset=["provider", "rate_type", "effective_date"],
                keep="last",
            )
            yield df.to_dict(orient="records")


def create_rate_source(path: str) -> RateRecordSource:
    """Factory Method — select concrete source implementation from path or type."""
    if path.endswith(".parquet"):
        return ParquetRateSource(path)
    raise ValueError(f"Unsupported rate source: {path}")
