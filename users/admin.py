"""Django admin для модели пользователя."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Админка пользователя с дополнительными полями профиля."""

    fieldsets = (
        *BaseUserAdmin.fieldsets,
        ("Профиль", {"fields": ("avatar", "phone_number", "country")}),
    )
    list_display = ("email", "username", "first_name", "last_name", "is_staff")
