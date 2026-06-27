"""Load-balancer health check — verifies Postgres and Redis connectivity."""

from django.core.cache import cache
from django.db import connection
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    """GET /api/health/ — used by ALB target group health checks."""

    def get(self, request):
        checks: dict[str, str] = {}

        try:
            connection.ensure_connection()
            checks["database"] = "ok"
        except Exception as exc:
            checks["database"] = str(exc)

        try:
            cache.set("health_check", "ok", 5)
            checks["redis"] = "ok" if cache.get("health_check") == "ok" else "fail"
        except Exception as exc:
            checks["redis"] = str(exc)

        healthy = all(value == "ok" for value in checks.values())
        return Response(
            {"status": "ok" if healthy else "degraded", "checks": checks},
            status=200 if healthy else 503,
        )
