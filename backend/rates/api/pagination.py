"""Shared DRF pagination helpers for history and ingested list endpoints."""

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from rates.api.serializers import RateSerializer


class HistoryPagination(PageNumberPagination):
    """Page-number pagination tuned for chart/table clients (max 200 via ?page_size=)."""

    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


class PaginatedRateListMixin:
    """Serialize and paginate a rate queryset — shared by history and ingested views."""

    pagination_class = HistoryPagination
    serializer_class = RateSerializer

    def paginate_rates(self, request, queryset) -> Response:
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        return paginator.get_paginated_response(self.serializer_class(page, many=True).data)
