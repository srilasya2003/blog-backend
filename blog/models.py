from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from PIL import Image


User = get_user_model()


def validate_image_file(value):
	if not value:
		return

	allowed_extensions = [".jpg", ".jpeg", ".png"]
	filename = value.name.lower()

	if not any(filename.endswith(ext) for ext in allowed_extensions):
		raise ValidationError("Only JPG, JPEG, and PNG files are allowed.")

	try:
		img = Image.open(value)
		img.verify()
		value.seek(0)
	except Exception:
		value.seek(0)
		raise ValidationError("Uploaded file is not a valid image.")


def post_image_upload_path(instance, filename):
	return f"users/{instance.author_id}/posts/{filename}"


class Category(models.Model):
	name = models.CharField(max_length=100)
	slug = models.SlugField(max_length=100, unique=True, blank=True)

	def save(self, *args, **kwargs):
		self.slug = slugify(self.name)
		super().save(*args, **kwargs)

	def __str__(self):
		return self.name


class Post(models.Model):
	title = models.CharField(max_length=200)
	slug = models.SlugField(max_length=200, unique=True, blank=True)
	content = models.TextField()
	author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
	category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="posts")
	image = models.ImageField(
		upload_to=post_image_upload_path,
		blank=True,
		null=True,
		validators=[validate_image_file],
	)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	is_published = models.BooleanField(default=False)

	def save(self, *args, **kwargs):
		self.slug = slugify(self.title)
		super().save(*args, **kwargs)

	def __str__(self):
		return self.title
