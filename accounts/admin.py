from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User
    list_display = ("username", "email", "is_staff", "role", "is_active")
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Profile", {"fields": ("bio", "profile_picture_url", "role")}),
    )
