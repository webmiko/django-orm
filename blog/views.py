"""Контроллеры приложения blog. CRUD для блоговой записи на CBV."""

from django.db.models import F
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

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


class PostCreateView(CreateView):
    """Создание новой блоговой записи."""

    model = BlogPost
    fields = ["title", "content", "preview", "is_published"]
    template_name = "blog/post_form.html"
    success_url = reverse_lazy("blog:post_list")


class PostUpdateView(UpdateView):
    """Редактирование блоговой записи. После сохранения — редирект на страницу статьи."""

    model = BlogPost
    fields = ["title", "content", "preview", "is_published"]
    template_name = "blog/post_form.html"
    context_object_name = "post"

    def get_success_url(self):
        return reverse("blog:post_detail", kwargs={"pk": self.object.pk})


class PostDeleteView(DeleteView):
    """Удаление блоговой записи с подтверждением."""

    model = BlogPost
    template_name = "blog/post_confirm_delete.html"
    context_object_name = "post"
    success_url = reverse_lazy("blog:post_list")
