"""Контроллеры приложения catalog.

Главная страница с выводом последних продуктов в консоль, страница контактов.
"""

import logging
from pathlib import Path

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from .models import Contact, Product

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
    return render(request, "catalog/home.html")


def contacts(request: HttpRequest) -> HttpResponse:
    """Страница контактов: данные из модели Contact (заполняются в админке)."""
    contact_list = Contact.objects.all()
    return render(
        request,
        "catalog/contacts.html",
        {"contact_list": contact_list},
    )
