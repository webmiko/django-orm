"""Тесты приложения blog."""

from io import BytesIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from blog.forms import BlogPostForm
from blog.models import BlogPost

User = get_user_model()


class BlogPostFormImageTest(TestCase):
    """Валидация превью (JPEG/PNG, размер)."""

    def test_valid_png_preview(self):
        buf = BytesIO()
        Image.new("RGB", (1, 1)).save(buf, format="PNG")
        file = SimpleUploadedFile("p.png", buf.getvalue(), content_type="image/png")
        form = BlogPostForm(
            data={"title": "Заголовок", "content": "Текст", "is_published": "on"},
            files={"preview": file},
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_rejects_invalid_image_magic(self):
        bad = SimpleUploadedFile("x.jpg", b"notimage", content_type="image/jpeg")
        form = BlogPostForm(
            data={"title": "T", "content": "C", "is_published": "on"},
            files={"preview": bad},
        )
        self.assertFalse(form.is_valid())
        self.assertIn("preview", form.errors)

    def test_rejects_oversize_with_patched_limit(self):
        png_header = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        biggish = SimpleUploadedFile("h.png", png_header, content_type="image/png")
        with patch("config.image_validation.MAX_UPLOAD_IMAGE_BYTES", 20):
            form = BlogPostForm(
                data={"title": "T", "content": "C", "is_published": "on"},
                files={"preview": biggish},
            )
            self.assertFalse(form.is_valid())
            self.assertIn("preview", form.errors)


class BlogCrudAuthTest(TestCase):
    """CRUD блога доступен только после входа."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="bloguser", email="blog@test.ru", password="secret-xyz-1"
        )

    def test_post_list_ok_for_anonymous(self):
        response = self.client.get(reverse("blog:post_list"))
        self.assertEqual(response.status_code, 200)

    def test_create_redirects_anonymous(self):
        response = self.client.get(reverse("blog:post_create"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_create_get_200_when_logged_in(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("blog:post_create"))
        self.assertEqual(response.status_code, 200)

    def test_create_post_saves_when_logged_in(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("blog:post_create"),
            {"title": "Статья", "content": "Текст", "is_published": "on"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(BlogPost.objects.count(), 1)
