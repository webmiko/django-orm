"""Общие миксины для форм Django."""

from django import forms


class StyleFormMixin:
    """Базовые классы Bootstrap 5 для виджетов; детали полей задаются в __init__ формы."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        for _name, field in self.fields.items():
            widget = field.widget
            if isinstance(field, forms.BooleanField):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, forms.Select | forms.SelectMultiple):
                widget.attrs.setdefault("class", "form-select")
            else:
                widget.attrs.setdefault("class", "form-control")
