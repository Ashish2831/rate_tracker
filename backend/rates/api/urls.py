"""API URL routing for rate endpoints."""

from django.urls import path

from rates.api.views import IngestRateView, LatestRatesView, RateHistoryView

urlpatterns = [
    path("rates/latest", LatestRatesView.as_view(), name="rates-latest"),
    path("rates/history", RateHistoryView.as_view(), name="rates-history"),
    path("rates/ingest", IngestRateView.as_view(), name="rates-ingest"),
]
