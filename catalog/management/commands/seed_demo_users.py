"""Создание демо-пользователей с разными ролями и тестовых товаров для ручной проверки."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import BaseCommand

from catalog.models import Category, Product

User = get_user_model()

DEMO_PASSWORD = "DemoPass1!"

USERS_SPEC = (
    ("demo_owner", ()),
    ("demo_moderator", ("Модератор продуктов",)),
    ("demo_content", ("Контент-менеджер",)),
    ("demo_plain", ()),
)


class Command(BaseCommand):
    """Пользователи: владелец, модератор каталога, контент-менеджер блога, обычный. Пароль у всех один."""

    help = (
        "Создаёт группы (setup_catalog_groups), демо-пользователей и товары для проверки прав. "
        f"Пароль для всех демо-логинов: {DEMO_PASSWORD}"
    )

    def handle(self, *args, **options):  # noqa: ARG002
        call_command("setup_catalog_groups")

        for username, group_names in USERS_SPEC:
            User.objects.filter(username=username).delete()
            user = User.objects.create_user(username=username, password=DEMO_PASSWORD)
            for gname in group_names:
                user.groups.add(Group.objects.get(name=gname))
            self.stdout.write(
                self.style.SUCCESS(f"Пользователь {username!r} (группы: {group_names or '—'})")
            )

        owner = User.objects.get(username="demo_owner")
        plain = User.objects.get(username="demo_plain")

        cat, _ = Category.objects.get_or_create(
            name="Демо-категория",
            defaults={"description": "Для ручной проверки"},
        )

        Product.objects.filter(name__startswith="Демо-товар").delete()
        Product.objects.create(
            name="Демо-товар черновик (владелец demo_owner)",
            description="Не в каталоге; карточка доступна владельцу и модератору.",
            category=cat,
            owner=owner,
            price=Decimal("100.00"),
            is_published=False,
        )
        pub = Product.objects.create(
            name="Демо-товар опубликован (владелец demo_plain)",
            description="В каталоге; редактирует только demo_plain; удалить может модератор.",
            category=cat,
            owner=plain,
            price=Decimal("250.50"),
            is_published=True,
        )

        draft = Product.objects.filter(name__startswith="Демо-товар черновик").first()
        self.stdout.write(self.style.SUCCESS("Товары «Демо-товар …» созданы."))
        if draft:
            self.stdout.write(f"  Черновик (проверка 404 без входа): /product/{draft.pk}/")
        self.stdout.write(f"  Опубликованный: /product/{pub.pk}/")
        self.stdout.write(
            self.style.WARNING(
                f"\nЛогины: demo_owner, demo_moderator, demo_content, demo_plain\n"
                f"Пароль у всех: {DEMO_PASSWORD}\n",
            ),
        )
