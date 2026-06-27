"""Observability middleware — logs requests exceeding SLOW_QUERY_THRESHOLD_MS."""

import logging
import time

from django.conf import settings
from django.db import connection

logger = logging.getLogger("rates.middleware")


class SlowQueryLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.perf_counter()
        initial_queries = len(connection.queries)

        response = self.get_response(request)

        duration_ms = (time.perf_counter() - start) * 1000
        query_count = len(connection.queries) - initial_queries

        if duration_ms >= settings.SLOW_QUERY_THRESHOLD_MS:
            logger.warning(
                "Slow request detected",
                extra={
                    "event": "slow_request",
                    "duration_ms": round(duration_ms, 2),
                    "path": request.path,
                    "method": request.method,
                    "status_code": response.status_code,
                    "query_count": query_count,
                },
            )

        return response
