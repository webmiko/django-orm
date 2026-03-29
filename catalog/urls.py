"""Catalog URL config."""

from django.urls import path

from .views import (
    CatalogListView,
    CategoryDetailView,
    CategoryIndexView,
    ContactsView,
    HomeView,
    ProductDetailView,
)

app_name = "catalog"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("product/<int:pk>/", ProductDetailView.as_view(), name="product_detail"),
    path("catalog/", CatalogListView.as_view(), name="catalog"),
    path("category/", CategoryIndexView.as_view(), name="category"),
    path("category/<int:pk>/", CategoryDetailView.as_view(), name="category_detail"),
    path("contacts/", ContactsView.as_view(), name="contacts"),
]
