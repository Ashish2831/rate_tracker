"""Permission classes for ingest and other protected API views."""

from rest_framework.permissions import BasePermission


class HasBearerToken(BasePermission):
    """Allow bearer token (webhook) or logged-in staff (DRF browsable API / dev)."""

    message = "Bearer token or staff login required."

    def has_permission(self, request, view):
        if request.auth is not None:
            return True
        user = request.user
        return bool(user and user.is_authenticated and user.is_staff)
