"""API URL routing for rate endpoints."""

from django.urls import path

from rates.api.health import HealthView
from rates.api.views import IngestRateView, IngestedRatesView, LatestRatesView, RateFiltersView, RateHistoryView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("rates/latest", LatestRatesView.as_view(), name="rates-latest"),
    path("rates/filters", RateFiltersView.as_view(), name="rates-filters"),
    path("rates/history", RateHistoryView.as_view(), name="rates-history"),
    path("rates/ingested", IngestedRatesView.as_view(), name="rates-ingested"),
    path("rates/ingest", IngestRateView.as_view(), name="rates-ingest"),
]
