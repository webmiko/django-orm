"""Контроллеры приложения catalog.

Главная страница с выводом последних продуктов в лог, каталог, категории, контакты.
Все представления реализованы на основе классов (CBV).

CRUD товаров: ModelForm и дженерики CreateView / UpdateView / DeleteView.
"""

import logging
from pathlib import Path

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView, View
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from .forms import ContactForm, ProductForm, SiteLoginForm, SiteUserCreationForm
from .mixins import ProductDeletePermissionMixin, ProductOwnerRequiredMixin
from .models import Category, Product

ENCODING = "utf-8"
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
LAST_PRODUCTS_LIMIT = 5


def _setup_logger() -> logging.Logger:
    """Настраивает и возвращает логгер для модуля."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    if logger.handlers:
        return logger
    base_dir = Path(__file__).resolve().parent.parent
    logs_dir = base_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    log_file = logs_dir / "catalog_views.log"
    file_handler = logging.FileHandler(log_file, mode="a", encoding=ENCODING)
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt=TIMESTAMP_FORMAT,
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger


logger = _setup_logger()


class RegisterView(CreateView):
    """Регистрация нового пользователя; после успеха — вход и редирект на главную."""

    form_class = SiteUserCreationForm
    template_name = "catalog/register.html"
    success_url = reverse_lazy("catalog:home")

    def form_valid(self, form):
        self.object = form.save()
        login(
            self.request,
            self.object,
            backend="django.contrib.auth.backends.ModelBackend",
        )
        messages.success(self.request, "Регистрация прошла успешно. Добро пожаловать!")
        return HttpResponseRedirect(self.get_success_url())


class SiteLoginView(LoginView):
    """Вход на сайт (не админка)."""

    form_class = SiteLoginForm
    template_name = "catalog/login.html"
    redirect_authenticated_user = True


class SiteLogoutView(LogoutView):
    """Выход (POST, как рекомендует Django)."""

    next_page = reverse_lazy("catalog:home")


class ProductDetailView(DetailView):
    """Страница одного товара. Черновики (не в каталоге) — только владельцу и модераторам."""

    model = Product
    template_name = "catalog/product_detail.html"
    context_object_name = "product"

    def get_queryset(self):
        base = Product.objects.select_related("category", "owner")
        user = self.request.user
        if not user.is_authenticated:
            return base.filter(is_published=True)
        if user.has_perm("catalog.can_unpublish_product") or user.has_perm(
            "catalog.delete_product",
        ):
            return base
        return base.filter(Q(is_published=True) | Q(owner=user))


# --- Управление товарами (CRUD) ---


class ProductManageListView(LoginRequiredMixin, ListView):
    """Список всех товаров со ссылками на просмотр, редактирование и удаление."""

    model = Product
    template_name = "catalog/product_manage_list.html"
    context_object_name = "products"

    def get_queryset(self):
        qs = Product.objects.select_related("category", "owner").order_by("name")
        user = self.request.user
        if user.has_perm("catalog.can_unpublish_product") or user.has_perm(
            "catalog.delete_product",
        ):
            return qs
        return qs.filter(owner=user)


class ProductCreateView(LoginRequiredMixin, CreateView):
    """Создание продукта через ProductForm."""

    model = Product
    form_class = ProductForm
    template_name = "catalog/product_form.html"
    success_url = reverse_lazy("catalog:product_manage")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class ProductUpdateView(LoginRequiredMixin, ProductOwnerRequiredMixin, UpdateView):
    """Редактирование продукта только владельцем."""

    model = Product
    form_class = ProductForm
    template_name = "catalog/product_form.html"
    success_url = reverse_lazy("catalog:product_manage")


class ProductDeleteView(LoginRequiredMixin, ProductDeletePermissionMixin, DeleteView):
    """Удаление: владелец или модератор с правом delete_product."""

    model = Product
    template_name = "catalog/product_confirm_delete.html"
    success_url = reverse_lazy("catalog:product_manage")
    context_object_name = "product"


class ProductPublishView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Публикация продукта (модератор, то же право, что и для снятия с публикации)."""

    permission_required = "catalog.can_unpublish_product"

    def post(self, request, pk: int, *_args, **_kwargs):
        product = get_object_or_404(Product, pk=pk)
        product.is_published = True
        product.save(update_fields=["is_published", "updated_at"])
        messages.success(request, "Продукт опубликован в каталоге.")
        return redirect("catalog:product_manage")


class ProductUnpublishView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Снятие продукта с публикации (кастомное право can_unpublish_product)."""

    permission_required = "catalog.can_unpublish_product"

    def post(self, request, pk: int, *_args, **_kwargs):
        product = get_object_or_404(Product, pk=pk)
        product.is_published = False
        product.save(update_fields=["is_published", "updated_at"])
        messages.success(request, "Продукт снят с публикации.")
        return redirect("catalog:product_manage")


class HomeView(View):
    """Главная страница. В лог выводятся последние N созданных продуктов."""

    def get(self, request, *_args, **_kwargs):
        latest = (
            Product.objects.filter(is_published=True)
            .select_related("category")
            .order_by("-created_at")[:LAST_PRODUCTS_LIMIT]
        )
        for product in latest:
            logger.info(
                "Последний продукт: id=%s, name=%s, price=%s, category=%s",
                product.pk,
                product.name,
                product.price,
                product.category.name,
            )
        return render(
            request,
            "catalog/home.html",
            {"latest_products": latest},
        )


class ContactsView(View):
    """Страница контактов: ModelForm обратной связи без публичного списка ПДн."""

    def get(self, request, *_args, **_kwargs):
        form = ContactForm()
        return render(request, "catalog/contacts.html", {"form": form})

    def post(self, request, *_args, **_kwargs):
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Спасибо! Ваше сообщение принято.")
            return redirect("catalog:contacts")
        return render(request, "catalog/contacts.html", {"form": form})


class CatalogListView(ListView):
    """Страница каталога: список товаров с фильтрами по категории, цене и сортировкой."""

    model = Product
    template_name = "catalog/catalog.html"
    context_object_name = "products"

    def get_queryset(self):
        queryset = Product.objects.filter(is_published=True).select_related("category")

        category_id_raw = self.request.GET.get("category")
        if category_id_raw is not None:
            try:
                category_id = int(category_id_raw)
            except ValueError:
                category_id = None
            if category_id is not None:
                queryset = queryset.filter(category_id=category_id)

        price = self.request.GET.get("price")
        if price == "low":
            queryset = queryset.filter(price__lt=1000)
        elif price == "medium":
            queryset = queryset.filter(price__gte=1000, price__lte=5000)
        elif price == "high":
            queryset = queryset.filter(price__gt=5000)

        sort = self.request.GET.get("sort", "name")
        if sort == "price-asc":
            queryset = queryset.order_by("price", "name")
        elif sort == "price-desc":
            queryset = queryset.order_by("-price", "name")
        else:
            queryset = queryset.order_by("name")

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        return context


class CategoryIndexView(View):
    """Страница «Категория»: товары первой категории или пустой список."""

    def get(self, request, *_args, **_kwargs):
        category = Category.objects.first()
        products = category.products.filter(is_published=True).order_by("name") if category else []
        return render(
            request,
            "catalog/category.html",
            {"category": category, "products": products},
        )


class CategoryDetailView(DetailView):
    """Страница категории по pk: товары выбранной категории."""

    model = Category
    template_name = "catalog/category.html"
    context_object_name = "category"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["products"] = self.object.products.filter(is_published=True).order_by("name")
        return context
