"""Тесты приложения blog.

Разграничение прав: CRUD блога доступен только группе «Контент-менеджер».
Черновики не отображаются в списке и недоступны по прямому URL.
"""

from io import BytesIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from blog.forms import BlogPostForm
from blog.models import BlogPost

User = get_user_model()


def _create_content_manager_group():
    group, _ = Group.objects.get_or_create(name="Контент-менеджер")
    perms = Permission.objects.filter(
        content_type__app_label="blog",
        codename__in=("add_blogpost", "change_blogpost", "delete_blogpost", "view_blogpost"),
    )
    group.permissions.set(perms)
    return group


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


class BlogCrudPermissionsTest(TestCase):
    """CRUD блога: только контент-менеджер, обычный пользователь — 403."""

    def setUp(self):
        self.plain = User.objects.create_user(
            username="plain", email="plain@test.ru", password="secret-xyz-1"
        )
        self.cm = User.objects.create_user(
            username="cm", email="cm@test.ru", password="secret-xyz-1"
        )
        cm_group = _create_content_manager_group()
        self.cm.groups.add(cm_group)

    def test_post_list_ok_for_anonymous(self):
        response = self.client.get(reverse("blog:post_list"))
        self.assertEqual(response.status_code, 200)

    def test_create_redirects_anonymous(self):
        response = self.client.get(reverse("blog:post_create"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_create_forbidden_for_plain_user(self):
        self.client.force_login(self.plain)
        response = self.client.get(reverse("blog:post_create"))
        self.assertEqual(response.status_code, 403)

    def test_create_allowed_for_content_manager(self):
        self.client.force_login(self.cm)
        response = self.client.get(reverse("blog:post_create"))
        self.assertEqual(response.status_code, 200)

    def test_create_post_sets_author(self):
        self.client.force_login(self.cm)
        response = self.client.post(
            reverse("blog:post_create"),
            {"title": "Статья", "content": "Текст", "is_published": "on"},
        )
        self.assertEqual(response.status_code, 302)
        post = BlogPost.objects.get()
        self.assertEqual(post.author, self.cm)

    def test_edit_forbidden_for_plain_user(self):
        post = BlogPost.objects.create(title="Пост", content="Текст", is_published=True)
        self.client.force_login(self.plain)
        response = self.client.get(reverse("blog:post_edit", kwargs={"pk": post.pk}))
        self.assertEqual(response.status_code, 403)

    def test_delete_forbidden_for_plain_user(self):
        post = BlogPost.objects.create(title="Пост", content="Текст", is_published=True)
        self.client.force_login(self.plain)
        response = self.client.post(reverse("blog:post_delete", kwargs={"pk": post.pk}))
        self.assertEqual(response.status_code, 403)

    def test_delete_allowed_for_content_manager(self):
        post = BlogPost.objects.create(title="Пост", content="Текст", is_published=True)
        self.client.force_login(self.cm)
        response = self.client.post(reverse("blog:post_delete", kwargs={"pk": post.pk}))
        self.assertRedirects(response, reverse("blog:post_list"))
        self.assertEqual(BlogPost.objects.count(), 0)


class BlogDraftAccessTest(TestCase):
    """Черновики блога не доступны по прямому URL."""

    def test_draft_returns_404(self):
        draft = BlogPost.objects.create(title="Черновик", content="Текст", is_published=False)
        response = self.client.get(reverse("blog:post_detail", kwargs={"pk": draft.pk}))
        self.assertEqual(response.status_code, 404)

    def test_published_returns_200(self):
        post = BlogPost.objects.create(title="Опубл", content="Текст", is_published=True)
        response = self.client.get(reverse("blog:post_detail", kwargs={"pk": post.pk}))
        self.assertEqual(response.status_code, 200)

    def test_draft_not_in_list(self):
        BlogPost.objects.create(title="Черновик", content="", is_published=False)
        BlogPost.objects.create(title="Видимый", content="", is_published=True)
        response = self.client.get(reverse("blog:post_list"))
        titles = [p.title for p in response.context["posts"]]
        self.assertNotIn("Черновик", titles)
        self.assertIn("Видимый", titles)
