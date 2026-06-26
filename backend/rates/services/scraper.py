import logging
from typing import Any

import requests
from requests import Response
from requests.exceptions import RequestException, Timeout

logger = logging.getLogger("rates.scraper")

DEFAULT_TIMEOUT = (5, 30)


class ScraperError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def fetch_rate_source(url: str, session: requests.Session | None = None) -> dict[str, Any]:
    """Fetch a rate source URL and return structured response metadata."""
    client = session or requests.Session()
    try:
        response: Response = client.get(url, timeout=DEFAULT_TIMEOUT)
    except Timeout as exc:
        logger.error("HTTP timeout", extra={"event": "scrape_timeout", "url": url, "error": str(exc)})
        raise ScraperError(f"Timeout fetching {url}") from exc
    except RequestException as exc:
        logger.error("HTTP error", extra={"event": "scrape_error", "url": url, "error": str(exc)})
        raise ScraperError(f"Request failed for {url}: {exc}") from exc

    if response.status_code >= 400:
        logger.warning(
            "HTTP error response",
            extra={
                "event": "scrape_http_error",
                "url": url,
                "status_code": response.status_code,
            },
        )
        raise ScraperError(
            f"HTTP {response.status_code} for {url}",
            status_code=response.status_code,
        )

    content_type = response.headers.get("Content-Type", "")
    if "application/json" in content_type:
        try:
            body: Any = response.json()
        except ValueError as exc:
            raise ScraperError(f"Invalid JSON from {url}") from exc
    else:
        body = {"raw_text": response.text[:10000]}

    return {
        "source_url": url,
        "status_code": response.status_code,
        "headers": dict(response.headers),
        "body": body,
    }


def parse_http_payload(payload: dict[str, Any]) -> dict[str, Any] | None:
    """Parse a JSON HTTP payload into a normalized rate record."""
    body = payload.get("body")
    if not isinstance(body, dict):
        return None

    record = {
        "provider": body.get("provider"),
        "rate_type": body.get("rate_type"),
        "rate_value": body.get("rate_value"),
        "effective_date": body.get("effective_date"),
        "ingestion_ts": body.get("ingestion_ts"),
        "currency": body.get("currency", "USD"),
        "source_url": payload.get("source_url"),
        "raw_response_id": body.get("raw_response_id"),
    }
    from rates.services.parser import parse_rate_record

    return parse_rate_record(record)
