"""Кастомная модель пользователя (AbstractUser, вход по email)."""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Пользователь сайта: вход по email, дополнительные поля для профиля."""

    email = models.EmailField("email", unique=True)
    avatar = models.ImageField("аватар", upload_to="avatars/", blank=True)
    phone_number = models.CharField("номер телефона", max_length=35, blank=True)
    country = models.CharField("страна", max_length=100, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]  # createsuperuser запросит username помимо email и пароля

    class Meta:
        verbose_name = "пользователь"
        verbose_name_plural = "пользователи"

    def __str__(self) -> str:
        return self.email
