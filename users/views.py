"""Контроллеры приложения users: регистрация, вход, выход, профиль."""

import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.core.mail import send_mail
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import UpdateView
from django.views.generic.edit import CreateView

from .forms import UserLoginForm, UserProfileForm, UserRegisterForm

AUTH_BACKEND = "django.contrib.auth.backends.ModelBackend"
WELCOME_EMAIL_SUBJECT = "Добро пожаловать!"
WELCOME_EMAIL_MESSAGE = "Спасибо, что зарегистрировались в нашем сервисе!"
MSG_REGISTER_SUCCESS = "Регистрация прошла успешно. Добро пожаловать!"
MSG_PROFILE_UPDATED = "Профиль обновлён."

logger = logging.getLogger(__name__)


class UserRegisterView(CreateView):
    """Регистрация нового пользователя; после успеха — вход и редирект на главную."""

    form_class = UserRegisterForm
    template_name = "users/register.html"
    success_url = reverse_lazy("catalog:home")

    def dispatch(self, request, *args, **kwargs):
        """Перенаправляет авторизованных пользователей на главную."""
        if request.user.is_authenticated:
            return HttpResponseRedirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Сохраняет пользователя, выполняет вход и отправляет приветственное письмо.

        Args:
            form: Валидная форма регистрации.

        Returns:
            HttpResponseRedirect на success_url.
        """
        self.object = form.save()
        login(self.request, self.object, backend=AUTH_BACKEND)
        self._send_welcome_email(self.object.email)
        messages.success(self.request, MSG_REGISTER_SUCCESS)
        return HttpResponseRedirect(self.get_success_url())

    @staticmethod
    def _send_welcome_email(user_email: str) -> None:
        """Отправляет приветственное письмо; при ошибке — логирует, не прерывает регистрацию."""
        try:
            send_mail(
                subject=WELCOME_EMAIL_SUBJECT,
                message=WELCOME_EMAIL_MESSAGE,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user_email],
            )
        except Exception:
            logger.exception("Не удалось отправить приветственное письмо")


class UserLoginView(LoginView):
    """Вход на сайт."""

    form_class = UserLoginForm
    template_name = "users/login.html"
    redirect_authenticated_user = True


class UserLogoutView(LogoutView):
    """Выход (POST, как рекомендует Django)."""

    next_page = reverse_lazy("catalog:home")


class UserProfileView(LoginRequiredMixin, UpdateView):
    """Редактирование профиля текущего пользователя."""

    form_class = UserProfileForm
    template_name = "users/profile.html"
    success_url = reverse_lazy("users:profile")

    def get_object(self, queryset=None):  # noqa: ARG002
        """Возвращает текущего пользователя как редактируемый объект."""
        return self.request.user

    def form_valid(self, form):
        """Сохраняет профиль и показывает сообщение об успехе."""
        messages.success(self.request, MSG_PROFILE_UPDATED)
        return super().form_valid(form)
