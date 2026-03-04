"""Контроллеры приложения catalog.

Главная страница с выводом последних продуктов в лог, каталог, категории, контакты.
Все представления реализованы на основе классов (CBV).
"""

import logging
from pathlib import Path

from django.shortcuts import redirect, render
from django.views.generic import DetailView, ListView, View

from .models import Category, Contact, Product

ENCODING = "utf-8"
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
LAST_PRODUCTS_LIMIT = 5


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


class ProductDetailView(DetailView):
    """Страница одного товара: все данные продукта по pk."""

    model = Product
    template_name = "catalog/product_detail.html"
    context_object_name = "product"

    def get_queryset(self):
        return Product.objects.select_related("category")


class HomeView(View):
    """Главная страница. В лог выводятся последние N созданных продуктов."""

    def get(self, request, *_args, **_kwargs):
        latest = Product.objects.order_by("-created_at")[:LAST_PRODUCTS_LIMIT]
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
    """Страница контактов: форма обратной связи и список контактов из БД."""

    def get(self, request, *_args, **_kwargs):
        contact_list = Contact.objects.all()
        return render(
            request,
            "catalog/contacts.html",
            {"contact_list": contact_list},
        )

    def post(self, request, *_args, **_kwargs):
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        message = request.POST.get("message", "").strip()
        if name and email and message:
            Contact.objects.create(name=name, email=email, message=message)
        return redirect("catalog:contacts")


class CatalogListView(ListView):
    """Страница каталога: список товаров с фильтрами по категории, цене и сортировкой."""

    model = Product
    template_name = "catalog/catalog.html"
    context_object_name = "products"

    def get_queryset(self):
        queryset = Product.objects.select_related("category")

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
            queryset = queryset.filter(price__lt=1000)
        elif price == "medium":
            queryset = queryset.filter(price__gte=1000, price__lte=5000)
        elif price == "high":
            queryset = queryset.filter(price__gt=5000)

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
        products = category.products.all().order_by("name") if category else []
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
        context["products"] = self.object.products.all().order_by("name")
        return context
