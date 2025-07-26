from django.db import models


class ContactMessage(models.Model):
    SUBJECT_CHOICES = [
        ("Support", "Support"),
        ("Feedback", "Feedback"),
        ("Business Inquiry", "Business Inquiry"),
        ("Other", "Other"),
    ]

    name = models.CharField(max_length=255)
    email = models.EmailField()
    subject = models.CharField(max_length=50, choices=SUBJECT_CHOICES)
    message = models.TextField()
    agree = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.subject}"

from django.conf import settings


class Category(models.Model):
    """Blog post categories."""

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    parent_category = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "categories"
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Tags for categorizing posts."""

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tags"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Post(models.Model):
    """Main blog post model."""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
    ]

    id = models.BigAutoField(primary_key=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    excerpt = models.TextField(blank=True)
    featured_image_url = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    view_count = models.PositiveIntegerField(default=0)
    seo_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    categories = models.ManyToManyField(Category, related_name="posts", blank=True)
    tags = models.ManyToManyField(Tag, related_name="posts", blank=True)
    liked_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="liked_posts",
        blank=True,
    )
    saved_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="saved_posts",
        blank=True,
    )

    class Meta:
        db_table = "posts"
        ordering = ["-published_at", "-created_at"]

    def __str__(self):
        return self.title


class UserSavedPost(models.Model):
    """Tracks which users saved which posts."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    saved_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "user_saved_posts"
        unique_together = ("user", "post")

    def __str__(self):
        return f"{self.user} saved {self.post}"


class Comment(models.Model):
    """Comments left on posts."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("spam", "Spam"),
    ]

    id = models.BigAutoField(primary_key=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    author_name = models.CharField(max_length=255, blank=True)
    author_email = models.EmailField(blank=True)
    content = models.TextField()
    parent_comment = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="replies",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = "comments"
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.author_name or self.user}" if self.user or self.author_name else "Comment"


class Media(models.Model):
    """Stores media file metadata."""

    id = models.BigAutoField(primary_key=True)
    file_url = models.URLField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    post = models.ForeignKey(Post, null=True, blank=True, on_delete=models.CASCADE, related_name="media")

    class Meta:
        db_table = "media"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.file_url


class PostRevision(models.Model):
    """Tracks revisions of post content."""

    id = models.BigAutoField(primary_key=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="revisions")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    version_number = models.PositiveIntegerField()

    class Meta:
        db_table = "post_revisions"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Revision {self.version_number} for {self.post}" 


class SiteSetting(models.Model):
    """Key-value settings for the site."""

    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)

    class Meta:
        db_table = "settings"

    def __str__(self):
        return self.key
