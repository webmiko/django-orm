"""Создание групп с правами для модераторов каталога и контент-менеджеров блога."""

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from blog.models import BlogPost
from catalog.models import Product

GROUP_MODERATOR = "Модератор продуктов"
GROUP_CONTENT = "Контент-менеджер"


class Command(BaseCommand):
    """Группы «Модератор продуктов» и «Контент-менеджер» с нужными Permission."""

    help = "Создаёт или обновляет группы прав: «Модератор продуктов», «Контент-менеджер»."

    def handle(self, *args, **options):  # noqa: ARG002
        product_ct = ContentType.objects.get_for_model(Product)
        blog_ct = ContentType.objects.get_for_model(BlogPost)

        mod_perms = Permission.objects.filter(
            content_type=product_ct,
            codename__in=("can_unpublish_product", "delete_product"),
        )
        if mod_perms.count() != 2:
            self.stdout.write(
                self.style.WARNING(
                    "Ожидались 2 права продукта (can_unpublish_product, delete_product). "
                    "Выполните migrate.",
                )
            )
        mod_group, created = Group.objects.get_or_create(name=GROUP_MODERATOR)
        mod_group.permissions.set(mod_perms)
        self.stdout.write(
            self.style.SUCCESS(
                f"Группа «{GROUP_MODERATOR}»: {'создана' if created else 'обновлена'}, "
                f"прав: {mod_perms.count()}.",
            )
        )

        content_codenames = (
            "add_blogpost",
            "change_blogpost",
            "delete_blogpost",
        )
        content_perms = Permission.objects.filter(
            content_type=blog_ct,
            codename__in=content_codenames,
        )
        content_group, created_c = Group.objects.get_or_create(name=GROUP_CONTENT)
        content_group.permissions.set(content_perms)
        self.stdout.write(
            self.style.SUCCESS(
                f"Группа «{GROUP_CONTENT}»: {'создана' if created_c else 'обновлена'}, "
                f"прав: {content_perms.count()}.",
            )
        )
