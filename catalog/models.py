"""Catalog models."""

from django.conf import settings
from django.core.validators import MaxLengthValidator
from django.db import models


class Category(models.Model):
    """Категория товаров."""

    name = models.CharField("наименование", max_length=150)
    description = models.TextField("описание", blank=True)

    class Meta:
        verbose_name = "категория"
        verbose_name_plural = "категории"

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    """Товар."""

    name = models.CharField("наименование", max_length=150)
    description = models.TextField("описание", blank=True)
    image = models.ImageField(
        "изображение",
        upload_to="products/",
        blank=True,
        null=True,
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products",
        verbose_name="категория",
    )
    price = models.DecimalField(
        "цена за покупку",
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    is_published = models.BooleanField("показывать в каталоге", default=True)
    created_at = models.DateTimeField("дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("дата последнего изменения", auto_now=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        verbose_name="владелец",
    )

    class Meta:
        verbose_name = "продукт"
        verbose_name_plural = "продукты"
        permissions = [
            ("can_unpublish_product", "Может снимать продукт с публикации"),
        ]

    def __str__(self) -> str:
        return self.name


class Contact(models.Model):
    """Контактные данные (обратная связь из админки)."""

    name = models.CharField("имя", max_length=150)
    email = models.EmailField("email")
    message = models.TextField("сообщение", validators=[MaxLengthValidator(10_000)])

    class Meta:
        verbose_name = "контакт"
        verbose_name_plural = "контакты"

    def __str__(self) -> str:
        return f"{self.name} ({self.email})"
