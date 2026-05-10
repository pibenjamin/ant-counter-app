from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission


class APIKeyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        key = request.headers.get("X-API-Key")
        if not key:
            return None
        if key == settings.API_SPECIES_KEY:
            return (AnonymousUser(), "api-key")
        raise AuthenticationFailed("Clé API invalide")

    def authenticate_header(self, request):
        return "X-API-Key"


class HasValidAccess(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated) or bool(request.auth)
