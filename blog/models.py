"""Blog models."""

from django.db import models


class BlogPost(models.Model):
    """Блоговая запись (статья)."""

    title = models.CharField("заголовок", max_length=200)
    content = models.TextField("содержимое", blank=True)
    preview = models.ImageField(
        "превью",
        upload_to="blog/",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField("дата создания", auto_now_add=True)
    is_published = models.BooleanField("признак публикации", default=False)
    view_count = models.PositiveIntegerField("количество просмотров", default=0)

    class Meta:
        verbose_name = "блоговая запись"
        verbose_name_plural = "блоговые записи"

    def __str__(self) -> str:
        return self.title
