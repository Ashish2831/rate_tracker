"""Typed exceptions for ingestion and webhook error handling."""


class InvalidIngestPayloadError(Exception):
    """Raised when a payload cannot be parsed into a valid rate record."""


class DuplicateRateError(Exception):
    """Raised when the same external_id was already ingested (idempotent no-op)."""
