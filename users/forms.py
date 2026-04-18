"""Формы приложения users: регистрация, вход, редактирование профиля."""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from config.form_mixins import StyleFormMixin
from config.image_validation import validate_uploaded_image_file

User = get_user_model()


class UserRegisterForm(StyleFormMixin, UserCreationForm):
    """Регистрация: email и пароль (password1/password2 добавляет UserCreationForm)."""

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email",)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs.update({"placeholder": "Email", "autocomplete": "email"})
        self.fields["password1"].widget.attrs.update(
            {"placeholder": "Пароль", "autocomplete": "new-password"}
        )
        self.fields["password2"].widget.attrs.update(
            {"placeholder": "Повторите пароль", "autocomplete": "new-password"}
        )

    def save(self, commit: bool = True):
        """Устанавливает username равным email, т.к. вход по email, а поле username обязательно в AbstractUser."""
        user = super().save(commit=False)
        user.username = user.email
        if commit:
            user.save()
        return user


class UserLoginForm(StyleFormMixin, AuthenticationForm):
    """Вход на сайт: email + пароль (Bootstrap-стили).

    AuthenticationForm внутри использует имя поля ``username``,
    но при USERNAME_FIELD = "email" подставляется email-поле модели;
    здесь меняем только лейбл и плейсхолдер под UI.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Email"
        self.fields["username"].widget.attrs.update(
            {"placeholder": "Email", "autocomplete": "email"}
        )
        self.fields["password"].widget.attrs.update(
            {"placeholder": "Пароль", "autocomplete": "current-password"}
        )


class UserProfileForm(StyleFormMixin, forms.ModelForm):
    """Редактирование профиля (без смены пароля)."""

    class Meta:
        model = User
        fields = ("first_name", "last_name", "phone_number", "country", "avatar")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["avatar"].widget.attrs.update(
            {"accept": "image/jpeg,image/png,.jpg,.jpeg,.png"}
        )
        self.fields["avatar"].required = False

    def clean_avatar(self):
        """JPEG/PNG, лимит размера — аналогично ProductForm и BlogPostForm."""
        avatar = self.cleaned_data.get("avatar")
        if not avatar:
            return avatar
        validate_uploaded_image_file(avatar)
        return avatar
