from django.urls import path

from .views import (
    CategoryListView,
    EmailVerificationConfirmView,
    EmailVerificationResendView,
    PostCreateView,
    PostDetailView,
    PostListView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    ProfileView,
    RegisterView,
)


urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path(
        "email-verification/confirm/",
        EmailVerificationConfirmView.as_view(),
        name="email-verification-confirm",
    ),
    path(
        "email-verification/resend/",
        EmailVerificationResendView.as_view(),
        name="email-verification-resend",
    ),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("password-reset/", PasswordResetRequestView.as_view(), name="password-reset"),
    path(
        "password-reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("posts/", PostListView.as_view(), name="post-list"),
    path("posts/create/", PostCreateView.as_view(), name="post-create"),
    path("posts/<int:pk>/", PostDetailView.as_view(), name="post-detail"),
]