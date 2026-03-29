"""Загрузка списка запрещённых подстрок для названия и описания товара.

Список задаётся вне кода приложения:
- файл (по умолчанию ``config/forbidden_product_words.txt`` в корне проекта);
- или путь в переменной окружения ``PRODUCT_FORBIDDEN_WORDS_FILE``;
- или перечень через запятую в ``PRODUCT_FORBIDDEN_WORDS`` (если файла нет).

Формат файла: одна фраза или слово на строку; пустые строки и строки, начинающиеся с ``#``, игнорируются.
Сравнение с текстом поля выполняется без учёта регистра (слова в файле можно писать в любом регистре).
"""

from __future__ import annotations

import os
from pathlib import Path

# Резерв, если ни одного источника внешней конфигурации нет (первый запуск без файла).
_DEFAULT_PRODUCT_FORBIDDEN_WORDS: tuple[str, ...] = (
    "казино",
    "криптовалюта",
    "крипта",
    "биржа",
    "дешево",
    "бесплатно",
    "обман",
    "полиция",
    "радар",
)


def _parse_forbidden_words_file(path: Path) -> list[str]:
    raw = path.read_text(encoding="utf-8")
    words: list[str] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        words.append(stripped.lower())
    return words


def _unique_preserve_order(items: list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return tuple(out)


def load_product_forbidden_words(base_dir: Path) -> tuple[str, ...]:
    """
    Возвращает кортеж запрещённых подстрок (в нижнем регистре).

    Приоритет:
    1. Файл из ``PRODUCT_FORBIDDEN_WORDS_FILE`` (относительно ``base_dir``, если путь не абсолютный).
    2. Файл ``<base_dir>/config/forbidden_product_words.txt``, если существует.
    3. ``PRODUCT_FORBIDDEN_WORDS`` в окружении (слова через запятую).
    4. Встроенный список по умолчанию.
    """
    explicit = os.getenv("PRODUCT_FORBIDDEN_WORDS_FILE", "").strip()
    if explicit:
        path = Path(explicit)
        if not path.is_absolute():
            path = base_dir / path
        if not path.is_file():
            msg = (
                "PRODUCT_FORBIDDEN_WORDS_FILE указывает на несуществующий файл: "
                f"{path.resolve()}"
            )
            raise RuntimeError(msg)
        return _unique_preserve_order(_parse_forbidden_words_file(path))

    default_path = base_dir / "config" / "forbidden_product_words.txt"
    if default_path.is_file():
        return _unique_preserve_order(_parse_forbidden_words_file(default_path))

    env_csv = os.getenv("PRODUCT_FORBIDDEN_WORDS", "").strip()
    if env_csv:
        parts = [p.strip().lower() for p in env_csv.split(",") if p.strip()]
        return _unique_preserve_order(parts)

    return _DEFAULT_PRODUCT_FORBIDDEN_WORDS
