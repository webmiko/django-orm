"""Создание групп «Модератор продуктов» и «Контент-менеджер» с правами."""

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Создаёт группы «Модератор продуктов» и «Контент-менеджер» с необходимыми правами."

    def handle(self, *_args, **_options):
        moderator, _ = Group.objects.get_or_create(name="Модератор продуктов")
        mod_perms = Permission.objects.filter(
            codename__in=("can_unpublish_product", "delete_product"),
            content_type__app_label="catalog",
        )
        moderator.permissions.set(mod_perms)
        self.stdout.write(
            self.style.SUCCESS(
                f"Группа «Модератор продуктов»: {list(mod_perms.values_list('codename', flat=True))}"
            )
        )

        content_mgr, _ = Group.objects.get_or_create(name="Контент-менеджер")
        blog_perms = Permission.objects.filter(
            content_type__app_label="blog",
            codename__in=("add_blogpost", "change_blogpost", "delete_blogpost", "view_blogpost"),
        )
        content_mgr.permissions.set(blog_perms)
        self.stdout.write(
            self.style.SUCCESS(
                f"Группа «Контент-менеджер»: {list(blog_perms.values_list('codename', flat=True))}"
            )
        )
