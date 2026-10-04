from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.test import APIClient
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from .models import Category, Post, post_image_upload_path


User = get_user_model()


class PostImageUploadPathTests(SimpleTestCase):
	def test_images_are_separated_by_author_id(self):
		first_author = type("Author", (), {"author_id": 42})()
		second_author = type("Author", (), {"author_id": 73})()

		self.assertEqual(
			post_image_upload_path(first_author, "photo.jpg"),
			"users/42/posts/photo.jpg",
		)
		self.assertEqual(
			post_image_upload_path(second_author, "photo.jpg"),
			"users/73/posts/photo.jpg",
		)


class JWTSessionTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			username="writer",
			email="writer@example.com",
			password="test-password-123",
		)
		self.category = Category.objects.create(name="News")
		self.post = Post.objects.create(
			title="Published story",
			content="Story content",
			author=self.user,
			category=self.category,
			is_published=True,
		)
		self.client = APIClient()

	def test_access_and_refresh_tokens_expire_after_one_hour(self):
		access = AccessToken.for_user(self.user)
		refresh = RefreshToken.for_user(self.user)

		self.assertEqual(access["exp"] - access["iat"], 3600)
		self.assertEqual(refresh["exp"] - refresh["iat"], 3600)
		self.assertEqual(api_settings.ACCESS_TOKEN_LIFETIME.total_seconds(), 3600)
		self.assertEqual(api_settings.REFRESH_TOKEN_LIFETIME.total_seconds(), 3600)

	def test_public_post_list_loads_with_an_expired_access_token(self):
		token = AccessToken.for_user(self.user)
		token["exp"] = int(timezone.now().timestamp()) - 1
		self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

		response = self.client.get("/api/posts/")

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data[0]["id"], self.post.id)

	def test_public_post_detail_loads_with_an_expired_access_token(self):
		token = AccessToken.for_user(self.user)
		token["exp"] = int(timezone.now().timestamp()) - 1
		self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

		response = self.client.get(f"/api/posts/{self.post.id}/")

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["id"], self.post.id)

	def test_private_profile_still_rejects_an_expired_access_token(self):
		token = AccessToken.for_user(self.user)
		token["exp"] = int(timezone.now().timestamp()) - 1
		self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

		response = self.client.get("/api/profile/")

		self.assertEqual(response.status_code, 401)

	def test_categories_endpoint_lists_categories_without_login(self):
		response = self.client.get("/api/categories/")

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data[0]["id"], self.category.id)
		self.assertEqual(response.data[0]["name"], self.category.name)


class PasswordResetTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			username="reset-user",
			email="reset@example.com",
			password="test-password-123",
		)

	@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
	def test_reset_request_sends_email_even_with_expired_bearer_token(self):
		token = AccessToken.for_user(self.user)
		token["exp"] = int(timezone.now().timestamp()) - 1
		client = APIClient()
		client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

		response = client.post(
			"/api/password-reset/",
			{"email": self.user.email},
			format="json",
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(mail.outbox), 1)
		self.assertEqual(mail.outbox[0].to, [self.user.email])
		self.assertIn("/reset-password/", mail.outbox[0].body)

	def test_password_reset_confirmation_does_not_require_access_token(self):
		client = APIClient()
		uid = urlsafe_base64_encode(force_bytes(self.user.pk))
		token = default_token_generator.make_token(self.user)
		client.credentials(HTTP_AUTHORIZATION="Bearer invalid-token")

		response = client.post(
			"/api/password-reset/confirm/",
			{
				"uid": uid,
				"token": token,
				"new_password": "FreshPass!8426",
			},
			format="json",
		)

		self.assertEqual(response.status_code, 200)
		self.user.refresh_from_db()
		self.assertTrue(self.user.check_password("FreshPass!8426"))


class CookieJWTAuthenticationTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			username="cookie-user",
			email="cookie@example.com",
			password="test-password-123",
		)
		self.category = Category.objects.create(name="Cookie Tests")
		self.client = APIClient(enforce_csrf_checks=True)

	def test_login_sets_httponly_tokens_and_profile_uses_access_cookie(self):
		csrf_response = self.client.get("/api/csrf/")
		self.assertIn("csrftoken", csrf_response.cookies)
		csrf_token = csrf_response.json()["csrfToken"]

		response = self.client.post(
			"/api/login/",
			{"email": self.user.email, "password": "test-password-123"},
			format="json",
			HTTP_X_CSRFTOKEN=csrf_token,
		)

		self.assertEqual(response.status_code, 200)
		self.assertNotIn("access", response.data)
		self.assertNotIn("refresh", response.data)
		self.assertTrue(response.cookies["accessToken"]["httponly"])
		self.assertTrue(response.cookies["refreshToken"]["httponly"])

		profile_response = self.client.get("/api/profile/")
		self.assertEqual(profile_response.status_code, 200)
		self.assertEqual(profile_response.data["id"], self.user.id)

	def test_cookie_authenticated_write_requires_csrf_header(self):
		csrf_response = self.client.get("/api/csrf/")
		self.assertIn("csrftoken", csrf_response.cookies)
		csrf_token = csrf_response.json()["csrfToken"]
		login_response = self.client.post(
			"/api/login/",
			{"email": self.user.email, "password": "test-password-123"},
			format="json",
			HTTP_X_CSRFTOKEN=csrf_token,
		)
		self.assertEqual(login_response.status_code, 200)

		response = self.client.post(
			"/api/posts/create/",
			{
				"title": "Cookie-authenticated post",
				"content": "Content",
				"category": self.category.id,
			},
			format="json",
		)

		self.assertEqual(response.status_code, 403)
