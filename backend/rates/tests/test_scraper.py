"""Unit tests for HTTP scrape transport and payload parsing."""

from decimal import Decimal

import pytest

from rates.services.parser import parse_scrape_payload
from rates.services.scraper import fetch_rate_source


@pytest.fixture
def sample_http_response():
    return {
        "provider": "Chase",
        "rate_type": "30yr_fixed_mortgage",
        "rate_value": 6.75,
        "effective_date": "2025-06-01",
        "ingestion_ts": "2025-06-01T12:00:00Z",
        "currency": "USD",
        "raw_response_id": "test-response-001",
    }


def test_parse_scrape_payload_matches_fixture(sample_http_response):
    payload = {
        "source_url": "https://www.chase.com/rates/30yr_fixed_mortgage",
        "body": sample_http_response,
    }
    parsed = parse_scrape_payload(payload)

    assert parsed is not None
    assert parsed.provider_name == "Chase"
    assert parsed.rate_type == "30yr_fixed_mortgage"
    assert parsed.rate_value == Decimal("6.75")
    assert parsed.external_id == "test-response-001"


def test_parse_scrape_payload_returns_none_for_non_dict_body():
    assert parse_scrape_payload({"source_url": "https://example.com", "body": "plain text"}) is None
    assert parse_scrape_payload({"source_url": "https://example.com", "body": {"raw_text": "html"}}) is None


def test_fetch_rate_source_success(mocker, sample_http_response):
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.json.return_value = sample_http_response

    mock_session = mocker.Mock()
    mock_session.get.return_value = mock_response

    result = fetch_rate_source("https://www.chase.com/rates/30yr_fixed_mortgage", session=mock_session)

    assert result["status_code"] == 200
    assert result["body"]["provider"] == "Chase"
    mock_session.get.assert_called_once()


def test_fetch_rate_source_http_error(mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 503
    mock_response.headers = {}
    mock_response.json.side_effect = ValueError()

    mock_session = mocker.Mock()
    mock_session.get.return_value = mock_response

    from rates.services.scraper import ScraperError

    with pytest.raises(ScraperError) as exc:
        fetch_rate_source("https://example.com/rates", session=mock_session)

    assert exc.value.status_code == 503


def test_fetch_rate_source_timeout(mocker):
    from requests.exceptions import Timeout

    from rates.services.scraper import ScraperError

    mock_session = mocker.Mock()
    mock_session.get.side_effect = Timeout("timed out")

    with pytest.raises(ScraperError):
        fetch_rate_source("https://example.com/rates", session=mock_session)
