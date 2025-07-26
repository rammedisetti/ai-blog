from django.contrib.auth.models import AbstractUser, Group
from django.db import models
import uuid


class InterestChoices(models.TextChoices):
    """Predefined interest options for users."""

    HOW_TOS = "how-tos", "How-tos"
    LATEST_TECH_NEWS = "latest-tech-news", "Latest tech news"
    EXPERT_OPINIONS = "expert-opinions", "Expert opinions"
    TECH_INSIGHTS = "tech-insights", "Tech insights"
    EXPERT_DEBATES = "expert-debates", "Expert debates"


class User(AbstractUser):
    """Custom user model with additional profile fields."""

    class Role(models.TextChoices):
        READER = "reader", "Reader"
        AUTHOR = "author", "Author"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile_picture_url = models.URLField(blank=True)
    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.READER
    )
    status = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profession = models.CharField(max_length=100, blank=True)
    interests = models.JSONField(default=list, blank=True)
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

    def save(self, *args, **kwargs):
        """Ensure user is placed in the correct group based on role."""
        super().save(*args, **kwargs)
        reader_group, _ = Group.objects.get_or_create(name=User.Role.READER)
        author_group, _ = Group.objects.get_or_create(name=User.Role.AUTHOR)
        if self.role == User.Role.AUTHOR:
            self.groups.add(author_group)
            self.groups.remove(reader_group)
        else:
            self.groups.add(reader_group)
            self.groups.remove(author_group)
