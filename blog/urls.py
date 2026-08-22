from django.urls import path

from .views import (
    CategoryListView,
    PostCreateView,
    PostDetailView,
    PostListView,
    RegisterView,
)


urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("posts/", PostListView.as_view(), name="post-list"),
    path("posts/create/", PostCreateView.as_view(), name="post-create"),
    path("posts/<int:pk>/", PostDetailView.as_view(), name="post-detail"),
]