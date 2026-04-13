"""Владелец продукта, кастомное право, default is_published=False."""

from django.contrib.auth.hashers import make_password
from django.db import migrations, models
import django.db.models.deletion


def _assign_product_owners(apps, schema_editor):
    Product = apps.get_model("catalog", "Product")
    User = apps.get_model("auth", "User")
    if not Product.objects.filter(owner__isnull=True).exists():
        return
    uid = User.objects.order_by("pk").values_list("pk", flat=True).first()
    if uid is None:
        User.objects.create(
            username="_pre_migrate_product_owner",
            password=make_password(None),
            is_active=False,
            is_staff=False,
        )
        uid = User.objects.get(username="_pre_migrate_product_owner").pk
    Product.objects.filter(owner__isnull=True).update(owner_id=uid)


def _noop_reverse(apps, schema_editor):
    """Обратная миграция владельца не откатывается автоматически."""


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0005_product_is_published_dz_26_1"),
        migrations.swappable_dependency("auth.User"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="owner",
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="owned_products",
                to="auth.user",
                verbose_name="владелец",
            ),
        ),
        migrations.RunPython(_assign_product_owners, _noop_reverse),
        migrations.AlterField(
            model_name="product",
            name="owner",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="owned_products",
                to="auth.user",
                verbose_name="владелец",
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="is_published",
            field=models.BooleanField(
                default=False,
                help_text="Новые товары по умолчанию не опубликованы до модерации.",
                verbose_name="показывать в каталоге",
            ),
        ),
        migrations.AlterModelOptions(
            name="product",
            options={
                "permissions": [
                    ("can_unpublish_product", "Может отменять публикацию продукта"),
                ],
                "verbose_name": "продукт",
                "verbose_name_plural": "продукты",
            },
        ),
    ]
