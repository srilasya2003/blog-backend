import hashlib
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.core.mail import send_mail
from django.db import models
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .authentication import OptionalJWTAuthentication
from .models import Category, Post
from .serializers import (
    CategorySerializer,
    EmailVerificationConfirmSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    PostSerializer,
    RegisterSerializer,
)


User = get_user_model()


def send_verification_email(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    verification_url = (
        f"{settings.FRONTEND_URL.rstrip('/')}/verify-email?"
        f"{urlencode({'uid': uid, 'token': token})}"
    )
    send_mail(
        "Verify your Brightline account",
        f"Open this link to verify your email address: {verification_url}",
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
    )


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        send_verification_email(serializer.instance)

        return Response(
            {
            "message": "Registration successful. Check your email to verify your account.",
                "user": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )


class EmailVerificationConfirmView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = EmailVerificationConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user_id = force_str(urlsafe_base64_decode(serializer.validated_data["uid"]))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {"detail": "This verification link is invalid or expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not default_token_generator.check_token(
            user, serializer.validated_data["token"]
        ):
            return Response(
                {"detail": "This verification link is invalid or expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.is_active:
            user.is_active = True
            user.save(update_fields=["is_active"])

        return Response({"message": "Email verified successfully."})


class EmailVerificationResendView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].strip().lower()
        email_digest = hashlib.sha256(email.encode("utf-8")).hexdigest()
        can_send = cache.add(
            f"email-verification-resend:{email_digest}", True, timeout=60
        )

        if can_send:
            user = User.objects.filter(email__iexact=email, is_active=False).first()
            if user:
                send_verification_email(user)

        return Response(
            {
                "message": (
                    "If an unverified account exists for this email, "
                    "a verification link has been sent."
                )
            }
        )


class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all().order_by("name")
    serializer_class = CategorySerializer
    authentication_classes = [OptionalJWTAuthentication]
    permission_classes = [permissions.AllowAny]


class PostListView(generics.ListAPIView):
    serializer_class = PostSerializer
    authentication_classes = [OptionalJWTAuthentication]
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = Post.objects.select_related("author", "category")
        if self.request.query_params.get("include_drafts") == "true":
            return queryset.order_by("-created_at")

        if self.request.user.is_authenticated:
            queryset = queryset.filter(
                models.Q(is_published=True) | models.Q(author=self.request.user)
            )
        else:
            queryset = queryset.filter(is_published=True)
        return queryset.order_by("-created_at")


class PostCreateView(generics.CreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PostSerializer
    authentication_classes = [OptionalJWTAuthentication]
    permission_classes = [
        permissions.AllowAny,
        IsAuthorOrReadOnly,
    ]

    def get_queryset(self):
        queryset = Post.objects.select_related("author", "category")
        if self.request.user.is_authenticated:
            return queryset.filter(
                models.Q(is_published=True) | models.Q(author=self.request.user)
            )
        return queryset.filter(is_published=True)


class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "id": request.user.id,
                "username": request.user.username,
                "email": request.user.email,
            }
        )


class PasswordResetRequestView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.filter(
            email__iexact=serializer.validated_data["email"]
        ).first()

        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = (
                f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}"
            )
            send_mail(
                "Reset your Brightline password",
                f"Use this link to reset your password: {reset_url}",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
            )

        return Response(
            {
                "message": (
                    "If an account exists with this email, "
                    "a reset link has been sent."
                )
            }
        )


class PasswordResetConfirmView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user_id = force_str(urlsafe_base64_decode(serializer.validated_data["uid"]))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {"detail": "This password reset link is invalid or expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not default_token_generator.check_token(
            user, serializer.validated_data["token"]
        ):
            return Response(
                {"detail": "This password reset link is invalid or expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_password(serializer.validated_data["new_password"], user)
        except Exception as error:
            return Response(
                {"detail": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        return Response({"message": "Password reset successfully."})