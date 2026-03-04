"""Catalog app tests.

Тесты представлений, моделей и URL: граничные случаи, 404, пустые данные, валидация.
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from catalog.models import Category, Contact, Product

# --- Views ---


class HomeViewTest(TestCase):
    """Главная страница: ответ, шаблон, контекст, пустая БД."""

    def test_home_returns_200(self):
        response = self.client.get(reverse("catalog:home"))
        self.assertEqual(response.status_code, 200)

    def test_home_uses_correct_template(self):
        response = self.client.get(reverse("catalog:home"))
        self.assertTemplateUsed(response, "catalog/home.html")

    def test_home_context_has_latest_products(self):
        response = self.client.get(reverse("catalog:home"))
        self.assertIn("latest_products", response.context)
        self.assertEqual(len(response.context["latest_products"]), 0)

    def test_home_shows_up_to_five_products(self):
        cat = Category.objects.create(name="Тест", description="")
        for i in range(7):
            Product.objects.create(
                name=f"Товар {i}",
                description="",
                category=cat,
                price=Decimal("100"),
            )
        response = self.client.get(reverse("catalog:home"))
        self.assertEqual(len(response.context["latest_products"]), 5)


class ProductDetailViewTest(TestCase):
    """Страница одного товара: 200 при существующем pk, 404 при отсутствии."""

    def test_product_detail_returns_200_for_existing_pk(self):
        cat = Category.objects.create(name="Кат", description="")
        product = Product.objects.create(
            name="Товар",
            description="Описание",
            category=cat,
            price=Decimal("99.99"),
        )
        response = self.client.get(reverse("catalog:product_detail", kwargs={"pk": product.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "catalog/product_detail.html")
        self.assertEqual(response.context["product"], product)

    def test_product_detail_returns_404_for_nonexistent_pk(self):
        response = self.client.get(reverse("catalog:product_detail", kwargs={"pk": 99999}))
        self.assertEqual(response.status_code, 404)


class ContactsViewTest(TestCase):
    """Контакты: GET 200, POST с валидными данными создаёт запись и редирект, пустой POST — редирект без создания."""

    def test_contacts_get_returns_200(self):
        response = self.client.get(reverse("catalog:contacts"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "catalog/contacts.html")
        self.assertIn("contact_list", response.context)

    def test_contacts_post_valid_creates_contact_and_redirects(self):
        response = self.client.post(
            reverse("catalog:contacts"),
            {"name": "Иван", "email": "ivan@test.ru", "message": "Текст сообщения"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("catalog:contacts"))
        self.assertEqual(Contact.objects.count(), 1)
        c = Contact.objects.get()
        self.assertEqual(c.name, "Иван")
        self.assertEqual(c.email, "ivan@test.ru")
        self.assertEqual(c.message, "Текст сообщения")

    def test_contacts_post_empty_redirects_without_creating(self):
        response = self.client.post(
            reverse("catalog:contacts"),
            {"name": "", "email": "", "message": ""},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Contact.objects.count(), 0)

    def test_contacts_post_partial_empty_does_not_create(self):
        response = self.client.post(
            reverse("catalog:contacts"),
            {"name": "Иван", "email": "", "message": "Текст"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Contact.objects.count(), 0)


class CatalogListViewTest(TestCase):
    """Каталог: 200, пустой список товаров/категорий не ломает страницу."""

    def test_catalog_list_returns_200(self):
        response = self.client.get(reverse("catalog:catalog"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "catalog/catalog.html")
        self.assertIn("products", response.context)
        self.assertIn("categories", response.context)
        self.assertEqual(list(response.context["products"]), [])
        self.assertEqual(list(response.context["categories"]), [])


class CategoryIndexViewTest(TestCase):
    """Страница «Категория» (первая): нет категорий — category None, products []; есть категория — товары."""

    def test_category_index_no_categories_returns_200(self):
        response = self.client.get(reverse("catalog:category"))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["category"])
        self.assertEqual(list(response.context["products"]), [])

    def test_category_index_with_category_returns_products(self):
        cat = Category.objects.create(name="Кат", description="")
        Product.objects.create(name="Товар", description="", category=cat, price=0)
        response = self.client.get(reverse("catalog:category"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["category"], cat)
        self.assertEqual(response.context["products"].count(), 1)


class CategoryDetailViewTest(TestCase):
    """Страница категории по pk: 200 при существующем pk, 404 при отсутствии."""

    def test_category_detail_returns_200_for_existing_pk(self):
        cat = Category.objects.create(name="Кат", description="")
        response = self.client.get(reverse("catalog:category_detail", kwargs={"pk": cat.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["category"], cat)
        self.assertIn("products", response.context)

    def test_category_detail_returns_404_for_nonexistent_pk(self):
        response = self.client.get(reverse("catalog:category_detail", kwargs={"pk": 99999}))
        self.assertEqual(response.status_code, 404)


# --- Models ---


class CategoryModelTest(TestCase):
    """Модель Category: создание, __str__."""

    def test_category_str(self):
        cat = Category(name="Электроника", description="")
        self.assertEqual(str(cat), "Электроника")

    def test_category_create_and_save(self):
        cat = Category.objects.create(name="Тест", description="Описание")
        self.assertIsNotNone(cat.pk)
        self.assertEqual(cat.name, "Тест")
        self.assertEqual(cat.description, "Описание")


class ProductModelTest(TestCase):
    """Модель Product: создание с категорией, __str__, цена по умолчанию."""

    def test_product_str(self):
        cat = Category.objects.create(name="Кат", description="")
        product = Product(name="Телефон", category=cat)
        self.assertEqual(str(product), "Телефон")

    def test_product_requires_category(self):
        cat = Category.objects.create(name="Кат", description="")
        product = Product.objects.create(
            name="Товар", description="", category=cat, price=Decimal("0")
        )
        self.assertEqual(product.category, cat)
        self.assertEqual(product.price, Decimal("0"))

    def test_product_default_price(self):
        cat = Category.objects.create(name="Кат", description="")
        product = Product.objects.create(name="Товар", description="", category=cat)
        self.assertEqual(product.price, Decimal("0"))


class ContactModelTest(TestCase):
    """Модель Contact: создание, __str__, валидация длины сообщения."""

    def test_contact_str(self):
        c = Contact(name="Иван", email="i@t.ru", message="Привет")
        self.assertEqual(str(c), "Иван (i@t.ru)")

    def test_contact_create(self):
        Contact.objects.create(name="Иван", email="ivan@test.ru", message="Сообщение")
        self.assertEqual(Contact.objects.count(), 1)

    def test_contact_message_max_length_validation(self):
        c = Contact(
            name="Иван",
            email="i@t.ru",
            message="x" * 10_001,
        )
        with self.assertRaises(ValidationError):
            c.full_clean()


# --- URLs ---


class CatalogUrlsTest(TestCase):
    """Проверка имён URL и разрешения маршрутов."""

    def test_home_url_resolves(self):
        url = reverse("catalog:home")
        self.assertEqual(url, "/")

    def test_product_detail_url_resolves(self):
        url = reverse("catalog:product_detail", kwargs={"pk": 1})
        self.assertEqual(url, "/product/1/")

    def test_contacts_url_resolves(self):
        url = reverse("catalog:contacts")
        self.assertEqual(url, "/contacts/")

    def test_catalog_url_resolves(self):
        url = reverse("catalog:catalog")
        self.assertEqual(url, "/catalog/")

    def test_category_url_resolves(self):
        url = reverse("catalog:category")
        self.assertEqual(url, "/category/")

    def test_category_detail_url_resolves(self):
        url = reverse("catalog:category_detail", kwargs={"pk": 2})
        self.assertEqual(url, "/category/2/")
