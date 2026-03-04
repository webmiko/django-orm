"""Django admin for blog."""

from django.contrib import admin

from .models import BlogPost


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "created_at", "is_published", "view_count")
    list_filter = ("is_published",)
    search_fields = ("title", "content")
