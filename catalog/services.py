"""Сервисный слой приложения catalog.

Бизнес-логика вынесена из представлений для повторного использования,
тестируемости и удобного подключения кеширования.
"""

from django.conf import settings
from django.core.cache import cache

from catalog.models import Product

PRODUCTS_CACHE_TIMEOUT = 60 * 15


def get_products_by_category(category_id: int) -> list[Product]:
    """Возвращает опубликованные товары указанной категории.

    При включённом кеше (``CACHE_ENABLED``) результат сохраняется в Redis
    на ``PRODUCTS_CACHE_TIMEOUT`` секунд.
    """
    cache_key = f"products_category_{category_id}"

    if settings.CACHE_ENABLED:
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

    products = list(
        Product.objects.filter(
            category_id=category_id,
            is_published=True,
        )
        .select_related("category")
        .order_by("name")
    )

    if settings.CACHE_ENABLED:
        cache.set(cache_key, products, PRODUCTS_CACHE_TIMEOUT)

    return products
