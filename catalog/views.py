"""Контроллеры приложения catalog.

Главная страница с выводом последних продуктов в лог, каталог, категории, контакты.
Все представления реализованы на основе классов (CBV).

CRUD товаров: ModelForm и дженерики CreateView / UpdateView / DeleteView.
Разграничение прав: владелец (owner), модератор (can_unpublish_product, delete_product).
"""

import logging
from pathlib import Path

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_page
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from .forms import ContactForm, ProductForm
from .models import Category, Product
from .services import get_products_by_category

ENCODING = "utf-8"
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
LAST_PRODUCTS_LIMIT = 5

PRODUCT_DETAIL_CACHE_TIMEOUT = 60 * 15
PRICE_LOW_THRESHOLD = 1000
PRICE_HIGH_THRESHOLD = 5000
MSG_CONTACT_SUCCESS = "Спасибо! Ваше сообщение принято."


def _setup_logger() -> logging.Logger:
    """Настраивает и возвращает логгер для модуля."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    if logger.handlers:
        return logger
    base_dir = Path(__file__).resolve().parent.parent
    logs_dir = base_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    log_file = logs_dir / "catalog_views.log"
    file_handler = logging.FileHandler(log_file, mode="a", encoding=ENCODING)
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt=TIMESTAMP_FORMAT,
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger


logger = _setup_logger()


class ProductOwnerRequiredMixin(UserPassesTestMixin):
    """Доступ только владельцу товара."""

    def test_func(self):
        product = self.get_object()
        return product.owner == self.request.user


class ProductOwnerOrModeratorDeleteMixin(UserPassesTestMixin):
    """Удаление: владелец или пользователь с правом delete_product."""

    def test_func(self):
        product = self.get_object()
        user = self.request.user
        return product.owner == user or user.has_perm("catalog.delete_product")


@method_decorator(cache_page(PRODUCT_DETAIL_CACHE_TIMEOUT), name="dispatch")
class ProductDetailView(DetailView):
    """Страница одного товара.

    Опубликованные — доступны всем (в т.ч. анонимам).
    Черновики — только владельцу и модераторам.
    """

    model = Product
    template_name = "catalog/product_detail.html"
    context_object_name = "product"

    def get_queryset(self):
        qs = Product.objects.select_related("category")
        user = self.request.user
        if user.is_authenticated:
            return qs.filter(
                Q(is_published=True) | Q(owner=user) | Q(pk__in=self._moderator_qs(qs))
            )
        return qs.filter(is_published=True)

    def _moderator_qs(self, qs):
        """PK черновиков, видимых модераторам."""
        if self.request.user.has_perm("catalog.can_unpublish_product"):
            return qs.filter(is_published=False).values("pk")
        return Product.objects.none().values("pk")


# --- Управление товарами (CRUD) ---


class ProductManageListView(LoginRequiredMixin, ListView):
    """Управление товарами: владелец видит свои, модератор — все."""

    model = Product
    template_name = "catalog/product_manage_list.html"
    context_object_name = "products"

    def get_queryset(self):
        user = self.request.user
        qs = Product.objects.select_related("category").order_by("name")
        if user.has_perm("catalog.can_unpublish_product"):
            return qs
        return qs.filter(owner=user)


class ProductCreateView(LoginRequiredMixin, CreateView):
    """Создание продукта: owner = текущий пользователь."""

    model = Product
    form_class = ProductForm
    template_name = "catalog/product_form.html"
    success_url = reverse_lazy("catalog:product_manage")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class ProductUpdateView(LoginRequiredMixin, ProductOwnerRequiredMixin, UpdateView):
    """Редактирование продукта — только владельцем."""

    model = Product
    form_class = ProductForm
    template_name = "catalog/product_form.html"
    success_url = reverse_lazy("catalog:product_manage")


class ProductDeleteView(LoginRequiredMixin, ProductOwnerOrModeratorDeleteMixin, DeleteView):
    """Удаление продукта: владелец или модератор с правом delete_product."""

    model = Product
    template_name = "catalog/product_confirm_delete.html"
    success_url = reverse_lazy("catalog:product_manage")
    context_object_name = "product"


class ProductPublishView(LoginRequiredMixin, View):
    """POST-действие: опубликовать / снять с публикации (модератор)."""

    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        if not request.user.has_perm("catalog.can_unpublish_product"):
            return HttpResponseForbidden()
        product.is_published = not product.is_published
        product.save(update_fields=["is_published"])
        return redirect("catalog:product_manage")


class HomeView(View):
    """Главная страница. В лог выводятся последние N созданных продуктов."""

    def get(self, request, *_args, **_kwargs):
        latest = (
            Product.objects.filter(is_published=True)
            .select_related("category")
            .order_by("-created_at")[:LAST_PRODUCTS_LIMIT]
        )
        for product in latest:
            logger.info(
                "Последний продукт: id=%s, name=%s, price=%s, category=%s",
                product.pk,
                product.name,
                product.price,
                product.category.name,
            )
        return render(
            request,
            "catalog/home.html",
            {"latest_products": latest},
        )


class ContactsView(View):
    """Страница контактов: ModelForm обратной связи без публичного списка ПДн."""

    def get(self, request, *_args, **_kwargs):
        form = ContactForm()
        return render(request, "catalog/contacts.html", {"form": form})

    def post(self, request, *_args, **_kwargs):
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, MSG_CONTACT_SUCCESS)
            return redirect("catalog:contacts")
        return render(request, "catalog/contacts.html", {"form": form})


class CatalogListView(ListView):
    """Страница каталога: список товаров с фильтрами по категории, цене и сортировкой."""

    model = Product
    template_name = "catalog/catalog.html"
    context_object_name = "products"

    def get_queryset(self):
        queryset = Product.objects.filter(is_published=True).select_related("category")

        category_id_raw = self.request.GET.get("category")
        if category_id_raw is not None:
            try:
                category_id = int(category_id_raw)
            except ValueError:
                category_id = None
            if category_id is not None:
                queryset = queryset.filter(category_id=category_id)

        price = self.request.GET.get("price")
        if price == "low":
            queryset = queryset.filter(price__lt=PRICE_LOW_THRESHOLD)
        elif price == "medium":
            queryset = queryset.filter(
                price__gte=PRICE_LOW_THRESHOLD, price__lte=PRICE_HIGH_THRESHOLD
            )
        elif price == "high":
            queryset = queryset.filter(price__gt=PRICE_HIGH_THRESHOLD)

        sort = self.request.GET.get("sort", "name")
        if sort == "price-asc":
            queryset = queryset.order_by("price", "name")
        elif sort == "price-desc":
            queryset = queryset.order_by("-price", "name")
        else:
            queryset = queryset.order_by("name")

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        return context


class CategoryIndexView(View):
    """Страница «Категория»: товары первой категории или пустой список."""

    def get(self, request, *_args, **_kwargs):
        category = Category.objects.first()
        products = get_products_by_category(category.pk) if category else []
        return render(
            request,
            "catalog/category.html",
            {"category": category, "products": products},
        )


class CategoryDetailView(DetailView):
    """Страница категории по pk: товары выбранной категории."""

    model = Category
    template_name = "catalog/category.html"
    context_object_name = "category"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["products"] = get_products_by_category(self.object.pk)
        return context
