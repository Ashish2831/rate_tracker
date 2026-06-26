import logging
from datetime import timedelta

from django.core.cache import cache
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from rates.api.authentication import BearerTokenAuthentication
from rates.api.permissions import HasBearerToken
from rates.api.serializers import IngestRateSerializer, LatestRateSerializer, RateSerializer
from rates.models import Rate
from rates.services.cache import latest_cache_key
from rates.services.ingestion import IngestionService
from rates.services.parser import normalize_provider_name

logger = logging.getLogger("rates.api")

CACHE_TTL_SECONDS = 60


class HistoryPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


class LatestRatesView(APIView):
    def get(self, request):
        rate_type = request.query_params.get("type")
        cache_key = latest_cache_key(rate_type)

        cached = cache.get(cache_key)
        if cached is not None:
            return Response({"count": len(cached), "results": cached, "cached": True})

        queryset = Rate.objects.select_related("provider").filter(rate_value__isnull=False)
        if rate_type:
            queryset = queryset.filter(rate_type=rate_type)

        rates = list(
            queryset.order_by("provider_id", "rate_type", "-effective_date", "-ingestion_ts").distinct(
                "provider_id", "rate_type"
            )
        )

        data = LatestRateSerializer(
            [
                {
                    "provider": rate.provider.name,
                    "rate_type": rate.rate_type,
                    "rate_value": rate.rate_value,
                    "effective_date": rate.effective_date,
                    "ingestion_ts": rate.ingestion_ts,
                    "currency": rate.currency,
                }
                for rate in rates
            ],
            many=True,
        ).data

        cache.set(cache_key, data, CACHE_TTL_SECONDS)
        return Response({"count": len(data), "results": data, "cached": False})


class RateHistoryView(APIView):
    pagination_class = HistoryPagination

    def get(self, request):
        provider = request.query_params.get("provider")
        rate_type = request.query_params.get("type")

        if not provider or not rate_type:
            return Response(
                {"error": "Both 'provider' and 'type' query parameters are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        date_from = request.query_params.get("from")
        date_to = request.query_params.get("to")

        if date_to:
            date_to = parse_date(date_to) if isinstance(date_to, str) else date_to
        else:
            date_to = timezone.now().date()

        if date_from:
            date_from = parse_date(date_from) if isinstance(date_from, str) else date_from
        else:
            date_from = date_to - timedelta(days=30)

        normalized = normalize_provider_name(provider).lower()

        queryset = (
            Rate.objects.select_related("provider")
            .filter(
                provider__normalized_name=normalized,
                rate_type=rate_type,
                effective_date__gte=date_from,
                effective_date__lte=date_to,
                rate_value__isnull=False,
            )
            .order_by("effective_date", "ingestion_ts")
        )

        paginator = HistoryPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = RateSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class IngestRateView(APIView):
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [HasBearerToken]

    def post(self, request):
        serializer = IngestRateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        payload = serializer.validated_data
        if "ingestion_ts" not in payload:
            payload["ingestion_ts"] = timezone.now()

        service = IngestionService()
        try:
            rate = service.ingest_from_api_payload(payload)
        except ValueError as exc:
            message = str(exc)
            if "Duplicate" in message:
                return Response({"message": message, "status": "duplicate"}, status=status.HTTP_200_OK)
            return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)

        logger.info(
            "Webhook ingest succeeded",
            extra={
                "event": "webhook_ingest",
                "provider": rate.provider.name,
                "rate_type": rate.rate_type,
            },
        )
        return Response(RateSerializer(rate).data, status=status.HTTP_201_CREATED)
