"""Контроллеры приложения catalog.

Главная страница с выводом последних продуктов в консоль, страница контактов.
"""

import logging
from pathlib import Path

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

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


def product_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """Страница одного товара: все данные продукта по pk."""
    product = get_object_or_404(Product.objects.select_related("category"), pk=pk)
    return render(request, "catalog/product_detail.html", {"product": product})


def home(request: HttpRequest) -> HttpResponse:
    """Главная страница. В консоль (лог) выводятся последние 5 созданных продуктов."""
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


def contacts(request: HttpRequest) -> HttpResponse:
    """Страница контактов: форма обратной связи и список контактов из БД."""
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        message = request.POST.get("message", "").strip()
        if name and email and message:
            Contact.objects.create(name=name, email=email, message=message)
        return redirect("catalog:contacts")
    contact_list = Contact.objects.all()
    return render(
        request,
        "catalog/contacts.html",
        {"contact_list": contact_list},
    )


def catalog_list(request: HttpRequest) -> HttpResponse:
    """Страница каталога: список товаров с фильтрами по категории, цене и сортировкой."""
    categories = Category.objects.all()
    products = Product.objects.select_related("category")

    category_id = request.GET.get("category")
    if category_id:
        try:
            products = products.filter(category_id=int(category_id))
        except ValueError:
            pass

    price = request.GET.get("price")
    if price == "low":
        products = products.filter(price__lt=1000)
    elif price == "medium":
        products = products.filter(price__gte=1000, price__lte=5000)
    elif price == "high":
        products = products.filter(price__gt=5000)

    sort = request.GET.get("sort", "name")
    if sort == "price-asc":
        products = products.order_by("price", "name")
    elif sort == "price-desc":
        products = products.order_by("-price", "name")
    else:
        products = products.order_by("name")

    return render(
        request,
        "catalog/catalog.html",
        {"products": products, "categories": categories},
    )


def category_index(request: HttpRequest) -> HttpResponse:
    """Страница «Категория»: товары первой категории или пустой список."""
    category = Category.objects.first()
    products = category.products.all().order_by("name") if category else []
    return render(
        request,
        "catalog/category.html",
        {"category": category, "products": products},
    )


def category_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """Страница категории по pk: товары выбранной категории."""
    category = get_object_or_404(Category, pk=pk)
    products = category.products.all().order_by("name")
    return render(
        request,
        "catalog/category.html",
        {"category": category, "products": products},
    )
