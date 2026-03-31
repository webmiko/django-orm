"""Формы приложения blog."""

from django import forms

from config.form_mixins import StyleFormMixin
from config.image_validation import validate_uploaded_image_file

from .models import BlogPost


class BlogPostForm(StyleFormMixin, forms.ModelForm):
    """Запись блога: стилизация и валидация превью (как у продукта в каталоге)."""

    class Meta:
        model = BlogPost
        fields = ("title", "content", "preview", "is_published")
        labels = {
            "title": "Заголовок",
            "content": "Содержимое",
            "preview": "Превью (изображение)",
            "is_published": "Опубликовать",
        }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["title"].widget.attrs.update(
            {"placeholder": "Заголовок статьи"}
        )
        self.fields["content"].widget.attrs.update(
            {"rows": 12, "placeholder": "Текст статьи"}
        )
        self.fields["preview"].widget.attrs.update(
            {
                "accept": "image/jpeg,image/png,.jpg,.jpeg,.png",
            }
        )
        self.fields["preview"].required = False

    def clean_preview(self):
        preview = self.cleaned_data.get("preview")
        if not preview:
            return preview
        validate_uploaded_image_file(preview)
        return preview
