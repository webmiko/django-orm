"""
Django settings for django-orm project.

PostgreSQL: задайте DB_NAME (и при необходимости DB_USER, DB_PASSWORD, DB_HOST, DB_PORT) в .env.
Если DB_NAME не задан — используется SQLite (файл db.sqlite3 в корне проекта), запасной вариант без Postgres.
"""

import os
from pathlib import Path

from django.urls import reverse_lazy
from dotenv import load_dotenv

from config.product_forbidden_words import load_product_forbidden_words

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DEBUG = os.getenv("DEBUG", "True").lower() == "true"

_SECRET_KEY_DEV = "django-insecure-dev-only-change-in-production"
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = _SECRET_KEY_DEV
    else:
        raise RuntimeError("Set SECRET_KEY in environment (e.g. .env)")
if not DEBUG and SECRET_KEY == _SECRET_KEY_DEV:
    raise RuntimeError("Do not use the default SECRET_KEY in production. Set SECRET_KEY in .env")


def _parse_allowed_hosts(value: str) -> list[str]:
    if not value or not value.strip():
        return []
    return [h.strip() for h in value.split(",") if h and h.strip()]


ALLOWED_HOSTS = _parse_allowed_hosts(os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1"))

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "catalog",
    "blog",
    "users",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# Database: PostgreSQL при заданном DB_NAME, иначе SQLite (запасной вариант)
if os.getenv("DB_NAME"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME", "django_orm"),
            "USER": os.getenv("DB_USER", "postgres"),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", "localhost"),
            "PORT": os.getenv("DB_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": str(BASE_DIR / "db.sqlite3"),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Список запрещённых подстрок для ProductForm: файл config/forbidden_product_words.txt или .env — см. product_forbidden_words.py
PRODUCT_FORBIDDEN_WORDS = load_product_forbidden_words(BASE_DIR)

AUTH_USER_MODEL = "users.User"

# Публичный вход на сайт (регистрация и CRUD для залогиненных пользователей).
LOGIN_URL = reverse_lazy("catalog:login")
LOGIN_REDIRECT_URL = reverse_lazy("catalog:home")
