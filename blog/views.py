"""Контроллеры приложения blog. CRUD для блоговой записи на CBV."""

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import F
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import BlogPostForm
from .models import BlogPost


class PostListView(ListView):
    """Список статей блога. В списке только опубликованные записи."""

    model = BlogPost
    template_name = "blog/post_list.html"
    context_object_name = "posts"

    def get_queryset(self):
        return BlogPost.objects.filter(is_published=True).order_by("-created_at")


class PostDetailView(DetailView):
    """Страница одной статьи. При просмотре увеличивается счётчик просмотров."""

    model = BlogPost
    template_name = "blog/post_detail.html"
    context_object_name = "post"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        BlogPost.objects.filter(pk=obj.pk).update(view_count=F("view_count") + 1)
        obj.refresh_from_db()
        return obj


class PostCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Создание записи: группа «Контент-менеджер» (право blog.add_blogpost)."""

    permission_required = "blog.add_blogpost"
    model = BlogPost
    form_class = BlogPostForm
    template_name = "blog/post_form.html"
    success_url = reverse_lazy("blog:post_list")


class PostUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Редактирование: право blog.change_blogpost."""

    permission_required = "blog.change_blogpost"
    model = BlogPost
    form_class = BlogPostForm
    template_name = "blog/post_form.html"
    context_object_name = "post"

    def get_success_url(self):
        return reverse("blog:post_detail", kwargs={"pk": self.object.pk})


class PostDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Удаление: право blog.delete_blogpost."""

    permission_required = "blog.delete_blogpost"
    model = BlogPost
    template_name = "blog/post_confirm_delete.html"
    context_object_name = "post"
    success_url = reverse_lazy("blog:post_list")
