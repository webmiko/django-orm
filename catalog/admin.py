"""Django admin for catalog."""

from django.contrib import admin

from .models import Category, Contact, Product


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "price", "category", "is_published")
    list_filter = ("category",)
    search_fields = ("name", "description")
