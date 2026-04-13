"""Кастомная команда загрузки тестовых данных каталога из фикстур."""

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand

from catalog.models import Category, Product

FIXTURE_DATA = "catalog_data"
FIXTURE_USER = "catalog_user"


class Command(BaseCommand):
    """Команда загрузки категорий и продуктов из фикстур с предварительной очисткой."""

    help = "Удаляет существующие данные каталога и загружает тестовые данные из фикстур."

    def handle(self, *args, **options):  # noqa: ARG002
        """Удаляет Product и Category, затем загружает фикстуру catalog_data."""
        self.stdout.write("Удаление существующих продуктов и категорий...")
        Product.objects.all().delete()
        Category.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("Данные удалены."))

        User = get_user_model()
        if not User.objects.exists():
            self.stdout.write(f"Загрузка пользователя-владельца ({FIXTURE_USER})...")
            call_command("loaddata", FIXTURE_USER, verbosity=1)

        self.stdout.write(f"Загрузка фикстуры {FIXTURE_DATA}...")
        try:
            call_command("loaddata", FIXTURE_DATA, verbosity=1)
            self.stdout.write(self.style.SUCCESS("Фикстура успешно загружена."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка загрузки: {e}"))
            raise
