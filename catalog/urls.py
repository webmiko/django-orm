"""Catalog URL config."""

from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.home, name="home"),
    path("product/<int:pk>/", views.product_detail, name="product_detail"),
    path("catalog/", views.catalog_list, name="catalog"),
    path("category/", views.category_index, name="category"),
    path("category/<int:pk>/", views.category_detail, name="category_detail"),
    path("contacts/", views.contacts, name="contacts"),
]
