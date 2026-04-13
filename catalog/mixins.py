"""Миксины проверки прав для представлений каталога."""

from django.contrib.auth.mixins import UserPassesTestMixin


class ProductOwnerRequiredMixin(UserPassesTestMixin):
    """Доступ только у владельца продукта (редактирование)."""

    def test_func(self) -> bool:
        product = self.get_object()
        return self.request.user.is_authenticated and product.owner_id == self.request.user.pk


class ProductDeletePermissionMixin(UserPassesTestMixin):
    """Удаление: владелец или пользователь с правом catalog.delete_product."""

    def test_func(self) -> bool:
        product = self.get_object()
        user = self.request.user
        return product.owner_id == user.pk or user.has_perm("catalog.delete_product")
