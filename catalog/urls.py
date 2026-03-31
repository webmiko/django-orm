"""Catalog URL config."""

from django.urls import path

from .views import (
    CatalogListView,
    CategoryDetailView,
    CategoryIndexView,
    ContactsView,
    HomeView,
    ProductCreateView,
    ProductDeleteView,
    ProductDetailView,
    ProductManageListView,
    ProductUpdateView,
    RegisterView,
    SiteLoginView,
    SiteLogoutView,
)

app_name = "catalog"

urlpatterns = [
    path("accounts/register/", RegisterView.as_view(), name="register"),
    path("accounts/login/", SiteLoginView.as_view(), name="login"),
    path("accounts/logout/", SiteLogoutView.as_view(), name="logout"),
    path("", HomeView.as_view(), name="home"),
    # Статические сегменты (`manage`, `add`, `edit`, `delete`) объявлены до `product/<pk>/`.
    path("product/manage/", ProductManageListView.as_view(), name="product_manage"),
    path("product/add/", ProductCreateView.as_view(), name="product_add"),
    path("product/<int:pk>/edit/", ProductUpdateView.as_view(), name="product_edit"),
    path("product/<int:pk>/delete/", ProductDeleteView.as_view(), name="product_delete"),
    path("product/<int:pk>/", ProductDetailView.as_view(), name="product_detail"),
    path("catalog/", CatalogListView.as_view(), name="catalog"),
    path("category/", CategoryIndexView.as_view(), name="category"),
    path("category/<int:pk>/", CategoryDetailView.as_view(), name="category_detail"),
    path("contacts/", ContactsView.as_view(), name="contacts"),
]
