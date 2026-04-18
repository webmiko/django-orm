"""Catalog app tests.

Тесты представлений, моделей и URL: граничные случаи, 404, пустые данные, валидация.
"""

from decimal import Decimal
from io import BytesIO
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from catalog.forms import ProductForm
from catalog.models import Category, Contact, Product

User = get_user_model()

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

    def setUp(self):
        from django.core.cache import cache

        cache.clear()
        self.user = User.objects.create_user(
            username="detailuser", email="detail@test.ru", password="test-pass-123"
        )

    def test_product_detail_returns_200_for_existing_pk(self):
        self.client.force_login(self.user)
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

    def test_product_detail_redirects_anonymous(self):
        cat = Category.objects.create(name="Кат", description="")
        product = Product.objects.create(
            name="Товар", description="", category=cat, price=Decimal("99.99")
        )
        response = self.client.get(reverse("catalog:product_detail", kwargs={"pk": product.pk}))
        self.assertEqual(response.status_code, 302)

    def test_product_detail_returns_404_for_nonexistent_pk(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("catalog:product_detail", kwargs={"pk": 99999}))
        self.assertEqual(response.status_code, 404)


class ContactsViewTest(TestCase):
    """Контакты: форма в контексте, без публичного списка ПДн."""

    def test_contacts_get_returns_200(self):
        response = self.client.get(reverse("catalog:contacts"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "catalog/contacts.html")
        self.assertIn("form", response.context)

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

    def test_contacts_post_empty_shows_form_errors_without_creating(self):
        response = self.client.post(
            reverse("catalog:contacts"),
            {"name": "", "email": "", "message": ""},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Contact.objects.count(), 0)
        self.assertFalse(response.context["form"].is_valid())

    def test_contacts_post_partial_empty_shows_errors_without_creating(self):
        response = self.client.post(
            reverse("catalog:contacts"),
            {"name": "Иван", "email": "", "message": "Текст"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Contact.objects.count(), 0)
        self.assertFalse(response.context["form"].is_valid())


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
        self.assertEqual(len(response.context["products"]), 1)


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

    # --- CRUD товаров (маршруты) ---
    def test_product_manage_url_resolves(self):
        self.assertEqual(reverse("catalog:product_manage"), "/product/manage/")

    def test_product_add_url_resolves(self):
        self.assertEqual(reverse("catalog:product_add"), "/product/add/")

    def test_product_edit_url_resolves(self):
        self.assertEqual(reverse("catalog:product_edit", kwargs={"pk": 3}), "/product/3/edit/")

    def test_product_delete_url_resolves(self):
        self.assertEqual(reverse("catalog:product_delete", kwargs={"pk": 4}), "/product/4/delete/")

    def test_auth_urls_resolves(self):
        self.assertEqual(reverse("users:register"), "/accounts/register/")
        self.assertEqual(reverse("users:login"), "/accounts/login/")
        self.assertEqual(reverse("users:logout"), "/accounts/logout/")


# --- Регистрация и вход на сайте ---


class SiteAuthViewsTest(TestCase):
    """Публичная регистрация и вход (не админка)."""

    def test_register_get_200(self):
        response = self.client.get(reverse("users:register"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/register.html")

    def test_register_post_creates_user_and_logs_in(self):
        response = self.client.post(
            reverse("users:register"),
            {
                "email": "u@example.com",
                "password1": "complex-pass-99-x",
                "password2": "complex-pass-99-x",
            },
        )
        self.assertRedirects(response, reverse("catalog:home"))
        self.assertTrue(User.objects.filter(email="u@example.com").exists())
        self.assertIn("_auth_user_id", self.client.session)

    def test_register_two_users_no_username_collision(self):
        for email in ("first@example.com", "second@example.com"):
            self.client.logout()
            response = self.client.post(
                reverse("users:register"),
                {
                    "email": email,
                    "password1": "complex-pass-99-x",
                    "password2": "complex-pass-99-x",
                },
            )
            self.assertRedirects(response, reverse("catalog:home"))
        self.assertEqual(User.objects.count(), 2)

    def test_register_redirects_authenticated_user(self):
        user = User.objects.create_user(username="existing", email="e@test.ru", password="pass-123")
        self.client.force_login(user)
        response = self.client.get(reverse("users:register"))
        self.assertEqual(response.status_code, 302)

    def test_login_get_200(self):
        response = self.client.get(reverse("users:login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/login.html")

    def test_login_post_succeeds(self):
        User.objects.create_user(
            username="logintest", email="login@test.ru", password="secret-abc-12"
        )
        response = self.client.post(
            reverse("users:login"),
            {"username": "login@test.ru", "password": "secret-abc-12"},
        )
        self.assertRedirects(response, reverse("catalog:home"))
        self.assertIn("_auth_user_id", self.client.session)


# --- Валидация ProductForm ---


class ProductFormValidationTest(TestCase):
    """Запрещённые слова, цена, изображение (формат и размер)."""

    def setUp(self):
        self.category = Category.objects.create(name="Категория", description="")

    def test_default_forbidden_words_loaded(self):
        for word in (
            "казино",
            "криптовалюта",
            "крипта",
            "биржа",
            "дешево",
            "бесплатно",
            "обман",
            "полиция",
            "радар",
        ):
            self.assertIn(word, settings.PRODUCT_FORBIDDEN_WORDS)

    @override_settings(PRODUCT_FORBIDDEN_WORDS=("уникальный_запрет_теста",))
    def test_forbidden_list_overridable_via_settings(self):
        form = ProductForm(
            data={
                "name": "Товар с уникальный_запрет_теста",
                "description": "Ок",
                "category": self.category.pk,
                "price": "1.00",
                "is_published": "on",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_name_rejects_forbidden_substring_case_insensitive(self):
        form = ProductForm(
            data={
                "name": "Товар КАЗИНО",
                "description": "Нормальное описание",
                "category": self.category.pk,
                "price": "1.00",
                "is_published": "on",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_description_rejects_forbidden_word_separately(self):
        form = ProductForm(
            data={
                "name": "Чистое имя",
                "description": "Здесь слово радар",
                "category": self.category.pk,
                "price": "1.00",
                "is_published": "on",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("description", form.errors)

    def test_negative_price_raises_validation_error(self):
        form = ProductForm(
            data={
                "name": "Товар",
                "description": "Описание",
                "category": self.category.pk,
                "price": "-1.00",
                "is_published": "on",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("price", form.errors)

    def test_valid_minimal_data(self):
        form = ProductForm(
            data={
                "name": "Товар",
                "description": "Описание",
                "category": self.category.pk,
                "price": "0",
                "is_published": "on",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    @staticmethod
    def _tiny_png_upload() -> SimpleUploadedFile:
        buf = BytesIO()
        Image.new("RGB", (1, 1), color=(200, 10, 10)).save(buf, format="PNG")
        return SimpleUploadedFile("one.png", buf.getvalue(), content_type="image/png")

    def test_valid_png_upload(self):
        form = ProductForm(
            data={
                "name": "С картинкой",
                "description": "Ок",
                "category": self.category.pk,
                "price": "10.00",
                "is_published": "on",
            },
            files={"image": self._tiny_png_upload()},
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_image_rejects_wrong_binary_magic(self):
        bad = SimpleUploadedFile("fake.jpg", b"not-an-image", content_type="image/jpeg")
        form = ProductForm(
            data={
                "name": "Товар",
                "description": "Ок",
                "category": self.category.pk,
                "price": "1.00",
                "is_published": "on",
            },
            files={"image": bad},
        )
        self.assertFalse(form.is_valid())
        self.assertIn("image", form.errors)

    def test_image_rejects_oversize_with_patched_limit(self):
        png_header = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        biggish = SimpleUploadedFile("huge.png", png_header, content_type="image/png")
        with patch("config.image_validation.MAX_UPLOAD_IMAGE_BYTES", 20):
            form = ProductForm(
                data={
                    "name": "Товар",
                    "description": "Ок",
                    "category": self.category.pk,
                    "price": "1.00",
                    "is_published": "on",
                },
                files={"image": biggish},
            )
            self.assertFalse(form.is_valid())
            self.assertIn("image", form.errors)


# --- CRUD товаров (представления, доступ по логину) ---


class ProductCrudViewsTest(TestCase):
    """Страницы управления товарами — только для авторизованных пользователей."""

    def setUp(self):
        self.category = Category.objects.create(name="Кат", description="")
        self.user = User.objects.create_user(
            username="cruduser", email="crud@test.ru", password="test-pass-123"
        )

    def test_product_manage_redirects_anonymous_to_login(self):
        response = self.client.get(reverse("catalog:product_manage"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_product_manage_get_200_when_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("catalog:product_manage"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "catalog/product_manage_list.html")

    def test_product_add_get_200_when_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("catalog:product_add"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "catalog/product_form.html")

    def test_product_add_post_creates_product(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("catalog:product_add"),
            {
                "name": "Новый товар",
                "description": "Описание",
                "category": str(self.category.pk),
                "price": "99.50",
                "is_published": "on",
            },
        )
        self.assertRedirects(response, reverse("catalog:product_manage"))
        self.assertEqual(Product.objects.count(), 1)
        product = Product.objects.get()
        self.assertEqual(product.name, "Новый товар")
        self.assertTrue(product.is_published)

    def test_product_edit_post_updates(self):
        self.client.force_login(self.user)
        product = Product.objects.create(
            name="Старое",
            description="",
            category=self.category,
            price=Decimal("1.00"),
        )
        response = self.client.post(
            reverse("catalog:product_edit", kwargs={"pk": product.pk}),
            {
                "name": "Новое имя",
                "description": "Текст",
                "category": str(self.category.pk),
                "price": "2.00",
            },
        )
        self.assertRedirects(response, reverse("catalog:product_manage"))
        product.refresh_from_db()
        self.assertEqual(product.name, "Новое имя")
        self.assertFalse(product.is_published)

    def test_product_delete_post_removes(self):
        self.client.force_login(self.user)
        product = Product.objects.create(
            name="Удалить",
            description="",
            category=self.category,
            price=Decimal("0"),
        )
        response = self.client.post(reverse("catalog:product_delete", kwargs={"pk": product.pk}))
        self.assertRedirects(response, reverse("catalog:product_manage"))
        self.assertEqual(Product.objects.count(), 0)

    def test_home_does_not_list_unpublished_products(self):
        Product.objects.create(
            name="Скрытый",
            description="",
            category=self.category,
            price=Decimal("1"),
            is_published=False,
        )
        response = self.client.get(reverse("catalog:home"))
        self.assertEqual(len(response.context["latest_products"]), 0)
