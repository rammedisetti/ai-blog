from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


class User(AbstractUser):
    """Custom user model with additional profile fields."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bio = models.TextField(blank=True)
    profile_picture_url = models.URLField(blank=True)
    role = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=100, blank=True)
    hobbies = models.TextField(blank=True)
    email_notifications = models.BooleanField(default=True)
    newsletter_subscription = models.BooleanField(default=True)
    comment_notifications = models.BooleanField(default=True)
    marketing_updates = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "users"
        ordering = ["username"]

    def __str__(self):
        return self.username
