from rest_framework import authentication, exceptions


class BearerTokenAuthentication(authentication.BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        auth_header = authentication.get_authorization_header(request).decode("utf-8")
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0] != self.keyword:
            raise exceptions.AuthenticationFailed("Invalid authorization header format.")

        from django.conf import settings

        if parts[1] != settings.INGEST_BEARER_TOKEN:
            raise exceptions.AuthenticationFailed("Invalid bearer token.")

        return (None, parts[1])
