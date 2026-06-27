"""Permission class requiring successful Bearer token authentication."""

from rest_framework.permissions import BasePermission


class HasBearerToken(BasePermission):
    message = "Bearer token authentication required."

    def has_permission(self, request, view):
        return request.auth is not None
