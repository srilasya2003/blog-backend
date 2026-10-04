"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.urls import include, path
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.authentication import SessionAuthentication
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from blog.serializers import EmailTokenObtainPairSerializer


class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        SessionAuthentication().enforce_csrf(request)
        response = super().post(request, *args, **kwargs)
        access_token = response.data.pop("access", None)
        refresh_token = response.data.pop("refresh", None)

        if access_token:
            response.set_cookie(
                settings.ACCESS_TOKEN_COOKIE_NAME,
                access_token,
                max_age=int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()),
                httponly=True,
                secure=not settings.DEBUG,
                samesite="Lax",
                path="/",
            )

        if refresh_token:
            response.set_cookie(
                settings.REFRESH_TOKEN_COOKIE_NAME,
                refresh_token,
                max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
                httponly=True,
                secure=not settings.DEBUG,
                samesite="Lax",
                path="/api/token/refresh/",
            )

        return response


class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        SessionAuthentication().enforce_csrf(request)
        refresh_token = request.COOKIES.get(settings.REFRESH_TOKEN_COOKIE_NAME)
        if not refresh_token:
            return Response(
                {"detail": "Refresh token missing."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = self.get_serializer(data={"refresh": refresh_token})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        response = Response({"message": "Session refreshed."})
        access_token = data.get("access")
        if access_token:
            response.set_cookie(
                settings.ACCESS_TOKEN_COOKIE_NAME,
                access_token,
                max_age=int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()),
                httponly=True,
                secure=not settings.DEBUG,
                samesite="Lax",
                path="/",
            )

        refresh_token = data.get("refresh")
        if refresh_token:
            response.set_cookie(
                settings.REFRESH_TOKEN_COOKIE_NAME,
                refresh_token,
                max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
                httponly=True,
                secure=not settings.DEBUG,
                samesite="Lax",
                path="/api/token/refresh/",
            )
        return response


def logout(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed."}, status=405)

    SessionAuthentication().enforce_csrf(request)
    response = JsonResponse({"message": "Logged out."})
    response.delete_cookie(
        settings.ACCESS_TOKEN_COOKIE_NAME,
        path="/",
        samesite="Lax",
    )
    response.delete_cookie(
        settings.REFRESH_TOKEN_COOKIE_NAME,
        path="/api/token/refresh/",
        samesite="Lax",
    )
    return response


@ensure_csrf_cookie
def csrf_cookie(request):
    return JsonResponse({"csrfToken": get_token(request)})

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("blog.urls")),
    path("api/csrf/", csrf_cookie, name="csrf-cookie"),
    path("api/login/", EmailTokenObtainPairView.as_view(), name="token-obtain"),
    path(
        "api/token/refresh/",
        CookieTokenRefreshView.as_view(),
        name="token-refresh",
    ),
    path("api/logout/", logout, name="logout"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
