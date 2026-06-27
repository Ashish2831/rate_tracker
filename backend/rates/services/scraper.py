"""HTTP transport for live rate-source URLs (tested; not wired to scheduled ingest)."""

import logging
from typing import Any

import requests
from requests import Response
from requests.exceptions import RequestException, Timeout

logger = logging.getLogger("rates.scraper")

DEFAULT_TIMEOUT = (5, 30)  # (connect, read) seconds


class ScraperError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def fetch_rate_source(url: str, session: requests.Session | None = None) -> dict[str, Any]:
    """Fetch a rate source URL and return structured response metadata (transport only — SRP)."""
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
        # Non-JSON responses are truncated and stored as raw text for inspection.
        body = {"raw_text": response.text[:10000]}

    return {
        "source_url": url,
        "status_code": response.status_code,
        "headers": dict(response.headers),
        "body": body,
    }
