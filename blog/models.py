from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify


User = get_user_model()


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
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	is_published = models.BooleanField(default=False)

	def save(self, *args, **kwargs):
		self.slug = slugify(self.title)
		super().save(*args, **kwargs)

	def __str__(self):
		return self.title
