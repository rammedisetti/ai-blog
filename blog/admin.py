from django.contrib import admin
from .models import (
    ContactMessage,
    Category,
    Tag,
    Post,
    Comment,
    Media,
    PostRevision,
    SiteSetting,
)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "subject", "created_at")
    search_fields = ("name", "email", "subject")
    list_filter = ("subject", "created_at")

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "parent_category", "created_at")
    search_fields = ("name", "slug")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name", "slug")


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "status", "published_at")
    search_fields = ("title", "slug")
    list_filter = ("status", "published_at")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("post", "author_name", "status", "created_at")
    search_fields = ("author_name", "author_email", "content")
    list_filter = ("status", "created_at")


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ("file_url", "uploaded_by", "uploaded_at")
    search_fields = ("file_url",)


@admin.register(PostRevision)
class PostRevisionAdmin(admin.ModelAdmin):
    list_display = ("post", "version_number", "created_at")
    search_fields = ("post__title",)


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ("key", "value")
    search_fields = ("key",)
