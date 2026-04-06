"""Формы приложения catalog."""

from decimal import Decimal

from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from config.form_mixins import StyleFormMixin
from config.image_validation import validate_uploaded_image_file

from .models import Contact, Product


class SiteLoginForm(StyleFormMixin, AuthenticationForm):
    """Вход на сайт (Bootstrap-поля)."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Имя пользователя"
        self.fields["username"].widget.attrs.update(
            {
                "autocomplete": "username",
                "placeholder": "Логин",
            }
        )
        self.fields["password"].widget.attrs.update(
            {
                "autocomplete": "current-password",
                "placeholder": "Пароль",
            }
        )


def _text_contains_forbidden_word(text: str) -> bool:
    """True, если в тексте встречается любая подстрока из settings.PRODUCT_FORBIDDEN_WORDS."""
    lowered = text.lower()
    return any(word in lowered for word in settings.PRODUCT_FORBIDDEN_WORDS)


class ContactForm(StyleFormMixin, forms.ModelForm):
    """Обратная связь на странице контактов (ModelForm + Bootstrap-атрибуты)."""

    class Meta:
        model = Contact
        fields = ("name", "email", "message")
        labels = {
            "name": "Имя",
            "email": "Почта",
            "message": "Сообщение",
        }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["name"].widget.attrs.update(
            {
                "class": "form-control contact-input",
                "placeholder": "Введите ваше имя",
                "autocomplete": "name",
            }
        )
        self.fields["email"].widget.attrs.update(
            {
                "class": "form-control contact-input",
                "placeholder": "example@mail.ru",
                "autocomplete": "email",
            }
        )
        self.fields["message"].widget.attrs.update(
            {
                "class": "form-control contact-input",
                "rows": "6",
                "placeholder": "Введите ваше сообщение...",
            }
        )


class ProductForm(StyleFormMixin, forms.ModelForm):
    """Карточка товара: поля модели, валидация (спам-слова, цена, изображение), стили Bootstrap."""

    class Meta:
        model = Product
        fields = (
            "name",
            "description",
            "image",
            "category",
            "price",
            "is_published",
        )
        labels = {
            "name": "Наименование",
            "description": "Описание",
            "image": "Изображение",
            "category": "Категория",
            "price": "Цена, ₽",
            "is_published": "Показывать в каталоге",
        }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["name"].widget.attrs.update(
            {
                "placeholder": "Название товара",
            }
        )
        self.fields["description"].widget.attrs.update(
            {
                "rows": 5,
                "placeholder": "Описание товара",
            }
        )
        self.fields["price"].widget.attrs.update(
            {
                "placeholder": "0.00",
                "min": "0",
                "step": "0.01",
            }
        )
        self.fields["image"].widget.attrs.update(
            {
                "accept": "image/jpeg,image/png,.jpg,.jpeg,.png",
            }
        )
        self.fields["image"].required = False

    def clean_name(self) -> str:
        """Запрещённые подстроки в наименовании."""
        name = self.cleaned_data.get("name") or ""
        if _text_contains_forbidden_word(name):
            raise ValidationError("В наименовании нельзя использовать слова из списка запрещённых.")
        return name

    def clean_description(self) -> str:
        """Запрещённые подстроки в описании."""
        description = self.cleaned_data.get("description") or ""
        if _text_contains_forbidden_word(description):
            raise ValidationError("В описании нельзя использовать слова из списка запрещённых.")
        return description

    def clean_price(self) -> Decimal:
        """Цена не отрицательная."""
        price = self.cleaned_data.get("price")
        if price is not None and price < 0:
            raise ValidationError("Цена продукта не может быть отрицательной.")
        return price

    def clean_image(self):
        """Изображение: JPEG/PNG, лимит размера (см. config.image_validation)."""
        image = self.cleaned_data.get("image")
        if not image:
            return image
        validate_uploaded_image_file(image)
        return image
