"""Pytest and pytest-django configuration."""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


def pytest_configure(config):  # noqa: ARG001
    import django

    django.setup()
