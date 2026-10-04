from django.conf import settings
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken


class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        raw_token = request.COOKIES.get(settings.ACCESS_TOKEN_COOKIE_NAME)
        if raw_token is None:
            return super().authenticate(request)

        validated_token = self.get_validated_token(raw_token.encode("utf-8"))
        user = self.get_user(validated_token)
        SessionAuthentication().enforce_csrf(request)
        return user, validated_token


class OptionalJWTAuthentication(CookieJWTAuthentication):
    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except InvalidToken:
            return None