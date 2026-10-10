# basically this file is used to convert the data from the database into JSON format so that it can be sent to the frontend. 
# It is also used to validate the data that is sent from the frontend before it is saved to the database.

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Category, Post, validate_image_file


User = get_user_model()


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
	username_field = User.EMAIL_FIELD
	email = serializers.EmailField()

	def validate(self, attrs):
		email = attrs["email"].strip()
		user = User.objects.filter(email__iexact=email).first()

		if user is None or not user.check_password(attrs["password"]):
			raise AuthenticationFailed("Invalid email or password.")

		if not user.is_active:
			raise AuthenticationFailed("This account is inactive.")

		refresh = self.get_token(user)
		return {
			"refresh": str(refresh),
			"access": str(refresh.access_token),
		}


class RegisterSerializer(serializers.ModelSerializer):
	password = serializers.CharField(write_only=True, min_length=8)

	class Meta:
		model = User
		fields = ["id", "username", "email", "password"]
		read_only_fields = ["id"]

	def validate_username(self, value):
		if User.objects.filter(username__iexact=value).exists():
			raise serializers.ValidationError(
				"This username is already registered. Please choose another."
			)
		return value

	def validate_email(self, value):
		if User.objects.filter(email__iexact=value).exists():
			raise serializers.ValidationError(
				"This email is already registered. Please try signing in."
			)
		return value

	def create(self, validated_data):
		validated_data["is_active"] = False
		return User.objects.create_user(**validated_data)


class EmailVerificationConfirmSerializer(serializers.Serializer):
	uid = serializers.CharField()
	token = serializers.CharField()


class PasswordResetRequestSerializer(serializers.Serializer):
	email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
	uid = serializers.CharField()
	token = serializers.CharField()
	new_password = serializers.CharField(write_only=True, min_length=8)


class CategorySerializer(serializers.ModelSerializer):
	class Meta:
		model = Category
		fields = ["id", "name", "slug"]
		read_only_fields = ["id", "slug"]


class PostSerializer(serializers.ModelSerializer):
	author = serializers.PrimaryKeyRelatedField(read_only=True)
	author_name = serializers.CharField(source="author.username", read_only=True)
	image = serializers.ImageField(required=False, allow_null=True)

	class Meta:
		model = Post
		fields = [
			"id",
			"title",
			"slug",
			"content",
			"author",
			"author_name",
			"category",
			"image",
			"created_at",
			"updated_at",
			"is_published",
		]
		read_only_fields = ["id", "slug", "created_at", "updated_at"]

	def validate_image(self, value):
		if value is not None:
			validate_image_file(value)
		return value


