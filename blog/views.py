from django.db import models
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from .models import Category, Post
from .serializers import CategorySerializer, PostSerializer, RegisterSerializer


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response(
            {
                "message": "Registration successful.",
                "user": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )


class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all().order_by("name")
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]


class PostListView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Post.objects.select_related(
            "author", "category"
        ).filter(
            models.Q(is_published=True) | models.Q(author=self.request.user)
        ).order_by("-created_at")


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
    permission_classes = [
        permissions.IsAuthenticated,
        IsAuthorOrReadOnly,
    ]

    def get_queryset(self):
        return Post.objects.select_related(
            "author", "category"
        ).filter(
            models.Q(is_published=True) | models.Q(author=self.request.user)
        )