"""DRF views for latest rates, history, and authenticated webhook ingest."""

import logging

from django.utils import timezone
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from rates.api.authentication import BearerTokenAuthentication
from rates.api.permissions import HasBearerToken
from rates.api.serializers import IngestRateSerializer, RateSerializer
from rates.services.exceptions import DuplicateRateError, InvalidIngestPayloadError
from rates.services.ingestion import IngestionService
from rates.services.ingested_rates_service import IngestedRatesService
from rates.services.latest_rates_service import LatestRatesCacheService
from rates.services.rate_filters_service import RateFiltersService
from rates.services.rate_history_service import RateHistoryService

logger = logging.getLogger("rates.api")


class HistoryPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


class ServiceAPIView(APIView):
    """Base view — delegates business logic to an injectable service class."""

    service_class = None

    def get_service(self):
        return self.service_class()


class LatestRatesView(ServiceAPIView):
    service_class = LatestRatesCacheService

    def get(self, request):
        data, cached = self.get_service().get_latest(
            rate_type=request.query_params.get("type"),
            provider=request.query_params.get("provider"),
        )
        return Response({"count": len(data), "results": data, "cached": cached})


class RateFiltersView(ServiceAPIView):
    service_class = RateFiltersService

    def get(self, request):
        return Response(self.get_service().get_options())


class RateHistoryView(ServiceAPIView):
    pagination_class = HistoryPagination
    service_class = RateHistoryService

    def get(self, request):
        provider = request.query_params.get("provider")
        rate_type = request.query_params.get("type")

        if not provider or not rate_type:
            return Response(
                {"error": "Both 'provider' and 'type' query parameters are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = self.get_service().get_history(
            provider=provider,
            rate_type=rate_type,
            date_from=request.query_params.get("from"),
            date_to=request.query_params.get("to"),
        )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        return paginator.get_paginated_response(RateSerializer(page, many=True).data)


class IngestedRatesView(ServiceAPIView):
    pagination_class = HistoryPagination
    service_class = IngestedRatesService

    def get(self, request):
        try:
            queryset = self.get_service().get_ingested(
                window_from=request.query_params.get("from"),
                window_to=request.query_params.get("to"),
                provider=request.query_params.get("provider"),
                rate_type=request.query_params.get("type"),
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        return paginator.get_paginated_response(RateSerializer(page, many=True).data)


class IngestRateView(ServiceAPIView):
    """Bearer-authenticated webhook for single-record ingest."""

    authentication_classes = [SessionAuthentication, BearerTokenAuthentication]
    permission_classes = [HasBearerToken]
    service_class = IngestionService

    def post(self, request):
        serializer = IngestRateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        payload = dict(serializer.validated_data)
        payload.setdefault("ingestion_ts", timezone.now())

        try:
            rate = self.get_service().ingest_from_api_payload(payload)
        except DuplicateRateError as exc:
            # Idempotent re-post returns 200, not an error.
            return Response({"message": str(exc), "status": "duplicate"}, status=status.HTTP_200_OK)
        except InvalidIngestPayloadError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        logger.info(
            "Webhook ingest succeeded",
            extra={
                "event": "webhook_ingest",
                "provider": rate.provider.name,
                "rate_type": rate.rate_type,
            },
        )
        return Response(RateSerializer(rate).data, status=status.HTTP_201_CREATED)
