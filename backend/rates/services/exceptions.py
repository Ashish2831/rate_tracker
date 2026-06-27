"""Typed exceptions for ingestion and webhook error handling."""


class IngestionError(Exception):
    """Base class for ingestion failures."""


class InvalidIngestPayloadError(IngestionError):
    """Raised when a payload cannot be parsed into a valid rate record."""


class DuplicateRateError(IngestionError):
    """Raised when an identical rate snapshot already exists (idempotent no-op)."""
