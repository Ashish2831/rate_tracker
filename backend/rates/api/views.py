import logging

from django.utils import timezone
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from rates.api.authentication import BearerTokenAuthentication
from rates.api.permissions import HasBearerToken
from rates.api.serializers import IngestRateSerializer, RateSerializer
from rates.services.exceptions import DuplicateRateError, InvalidIngestPayloadError
from rates.services.ingestion import IngestionService
from rates.services.latest_rates_service import LatestRatesCacheService
from rates.services.rate_history_service import RateHistoryService

logger = logging.getLogger("rates.api")


class HistoryPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


class LatestRatesView(APIView):
    service_class = LatestRatesCacheService

    def get_service(self) -> LatestRatesCacheService:
        return self.service_class()

    def get(self, request):
        rate_type = request.query_params.get("type")
        data, cached = self.get_service().get_latest(rate_type)
        return Response({"count": len(data), "results": data, "cached": cached})


class RateHistoryView(APIView):
    pagination_class = HistoryPagination
    service_class = RateHistoryService

    def get_service(self) -> RateHistoryService:
        return self.service_class()

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

        paginator = HistoryPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = RateSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class IngestRateView(APIView):
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [HasBearerToken]
    service_class = IngestionService

    def get_service(self) -> IngestionService:
        return self.service_class()

    def post(self, request):
        serializer = IngestRateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        payload = serializer.validated_data
        if "ingestion_ts" not in payload:
            payload["ingestion_ts"] = timezone.now()

        try:
            rate = self.get_service().ingest_from_api_payload(payload)
        except DuplicateRateError as exc:
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
