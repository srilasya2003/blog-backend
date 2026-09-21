# basically this file is used to convert the data from the database into JSON format so that it can be sent to the frontend. 
# It is also used to validate the data that is sent from the frontend before it is saved to the database.

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Category, Post


User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
	password = serializers.CharField(write_only=True, min_length=8)

	class Meta:
		model = User
		fields = ["id", "username", "email", "password"]
		read_only_fields = ["id"]

	def create(self, validated_data):
		return User.objects.create_user(**validated_data)


class CategorySerializer(serializers.ModelSerializer):
	class Meta:
		model = Category
		fields = ["id", "name", "slug"]
		read_only_fields = ["id", "slug"]


class PostSerializer(serializers.ModelSerializer):
	author = serializers.PrimaryKeyRelatedField(read_only=True)

	class Meta:
		model = Post
		fields = [
			"id",
			"title",
			"slug",
			"content",
			"author",
			"category",
			"image",
			"created_at",
			"updated_at",
			"is_published",
		]
		read_only_fields = ["id", "slug", "created_at", "updated_at"]


