"""API integration tests — require Postgres and Redis (run via make test in Docker)."""

from datetime import date
from decimal import Decimal

import pytest
from django.core.cache import cache
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from rates.models import Provider, Rate, RawResponse


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def sample_rate(db):
    provider = Provider.objects.create(name="Chase", normalized_name="chase")
    raw = RawResponse.objects.create(
        external_id="api-test-001",
        source_url="https://chase.com/rates",
        raw_body={"provider": "Chase"},
        fetched_at=timezone.now(),
        parse_status="success",
    )
    return Rate.objects.create(
        provider=provider,
        rate_type="30yr_fixed_mortgage",
        rate_value=Decimal("6.5000"),
        effective_date=date.today(),
        ingestion_ts=timezone.now(),
        currency="USD",
        raw_response=raw,
    )


@pytest.mark.django_db
def test_latest_rates_endpoint(api_client, sample_rate):
    cache.clear()
    response = api_client.get("/api/rates/latest")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] >= 1
    assert response.data["results"][0]["provider"] == "Chase"


@pytest.mark.django_db
def test_latest_rates_cached(api_client, sample_rate):
    cache.clear()
    first = api_client.get("/api/rates/latest")
    second = api_client.get("/api/rates/latest")

    assert first.data["cached"] is False
    assert second.data["cached"] is True


@pytest.mark.django_db
def test_history_endpoint_requires_params(api_client):
    response = api_client.get("/api/rates/history")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_history_endpoint_paginated(api_client, sample_rate):
    response = api_client.get(
        "/api/rates/history",
        {"provider": "Chase", "type": "30yr_fixed_mortgage"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert "results" in response.data
    assert len(response.data["results"]) >= 1


@pytest.mark.django_db
def test_ingest_requires_auth(api_client):
    response = api_client.post(
        "/api/rates/ingest",
        {
            "provider": "Chase",
            "rate_type": "30yr_fixed_mortgage",
            "rate_value": "6.75",
            "effective_date": str(date.today()),
        },
        format="json",
    )
    assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


@pytest.mark.django_db
def test_ingest_with_valid_token(api_client, settings):
    cache.clear()
    response = api_client.post(
        "/api/rates/ingest",
        {
            "provider": "Chase",
            "rate_type": "savings_easy_access",
            "rate_value": "4.50",
            "effective_date": str(date.today()),
            "raw_response_id": "webhook-test-001",
        },
        format="json",
        HTTP_AUTHORIZATION=f"Bearer {settings.INGEST_BEARER_TOKEN}",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["rate_type"] == "savings_easy_access"


@pytest.mark.django_db
def test_ingest_validation_error(api_client, settings):
    response = api_client.post(
        "/api/rates/ingest",
        {
            "provider": "Chase",
            "rate_type": "savings_easy_access",
            "rate_value": "-1.00",
            "effective_date": str(date.today()),
        },
        format="json",
        HTTP_AUTHORIZATION=f"Bearer {settings.INGEST_BEARER_TOKEN}",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "errors" in response.data
