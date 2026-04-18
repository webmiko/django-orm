"""Создание демо-пользователей для проверки разграничения прав."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from catalog.models import Category, Product

User = get_user_model()

DEMO_PASSWORD = "DemoPass1!"

DEMO_USERS = [
    {"email": "demo_owner@test.ru", "username": "demo_owner", "groups": []},
    {
        "email": "demo_moderator@test.ru",
        "username": "demo_moderator",
        "groups": ["Модератор продуктов"],
    },
    {"email": "demo_content@test.ru", "username": "demo_content", "groups": ["Контент-менеджер"]},
    {"email": "demo_plain@test.ru", "username": "demo_plain", "groups": []},
]


class Command(BaseCommand):
    help = "Создаёт демо-пользователей (demo_owner, demo_moderator, demo_content, demo_plain) и тестовые товары."

    def handle(self, *_args, **_options):
        users = {}
        for info in DEMO_USERS:
            user, created = User.objects.get_or_create(
                email=info["email"],
                defaults={"username": info["username"]},
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save()
            for group_name in info["groups"]:
                group = Group.objects.filter(name=group_name).first()
                if group:
                    user.groups.add(group)
            users[info["username"]] = user
            status = "создан" if created else "уже существует"
            self.stdout.write(f"  {info['username']} ({info['email']}) — {status}")

        category, _ = Category.objects.get_or_create(
            name="Демо-категория", defaults={"description": "Категория для проверки прав"}
        )

        draft, created = Product.objects.get_or_create(
            name="Черновик (demo_owner)",
            defaults={
                "description": "Товар-черновик для проверки доступа",
                "category": category,
                "price": 100,
                "is_published": False,
                "owner": users["demo_owner"],
            },
        )
        if created:
            self.stdout.write(f"  Черновик: /product/{draft.pk}/")

        published, created = Product.objects.get_or_create(
            name="Опубликованный (demo_plain)",
            defaults={
                "description": "Опубликованный товар",
                "category": category,
                "price": 500,
                "is_published": True,
                "owner": users["demo_plain"],
            },
        )
        if created:
            self.stdout.write(f"  Опубликованный: /product/{published.pk}/")

        self.stdout.write(
            self.style.SUCCESS(f"\nПароль для всех демо-пользователей: {DEMO_PASSWORD}")
        )
