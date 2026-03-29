# django-orm

Django-проект с Poetry, PostgreSQL, линтерами и тестами.

## Виртуальное окружение (Poetry)

```bash
# Установка зависимостей
poetry install

# Активация оболочки (опционально)
poetry shell
```

## База данных (PostgreSQL)

В проекте используется только PostgreSQL.

### 1. Установка и запуск PostgreSQL (macOS)

```bash
# Homebrew (PostgreSQL 18)
brew install postgresql@18
brew services start postgresql@18

# Добавьте в PATH (в ~/.zshrc или один раз в терминале):
export PATH="/opt/homebrew/opt/postgresql@18/bin:$PATH"
```

После установки в системе будет пользователь с вашим именем ОС (без пароля по умолчанию). Для создания БД и отдельного пользователя подключитесь суперпользователем: на macOS часто это ваш же логин, например `psql -d postgres` или `psql postgres`.

### 2. Создание базы и пользователя

```bash
psql -d postgres
```

В psql выполните (при необходимости смените пароль и повторите его в `.env`):

```sql
CREATE USER django_orm_user WITH PASSWORD 'django_orm_password';
CREATE DATABASE django_orm OWNER django_orm_user ENCODING 'UTF8';
\q
```

### 3. Настройка .env

В `.env` должны быть заданы (уже заполнено в примере):

- `DB_NAME=django_orm`
- `DB_USER=django_orm_user`
- `DB_PASSWORD=django_orm_password`
- `DB_HOST=localhost`
- `DB_PORT=5432`

### 4. Миграции

```bash
poetry run python manage.py migrate
```

## Локальный сервер (HTML)

```bash
poetry run python manage.py runserver 8080
```

Откройте в браузере: http://127.0.0.1:8080/ (админка: http://127.0.0.1:8080/admin/)

## Форматтеры и линтеры

```bash
# Проверка (Ruff + Black)
poetry run ruff check .
poetry run ruff format --check .
poetry run black --check .

# Исправление / форматирование
poetry run ruff check --fix .
poetry run ruff format .
poetry run black .
poetry run isort .
```

## Тесты

```bash
poetry run pytest
# или
poetry run python manage.py test
```

## Шаблоны и статика (магазин)

В проекте используются шаблоны и стили, адаптированные из папки **web_app** (референсный прототип, в репозиторий не входит):

- **Базовый шаблон**: `catalog/templates/catalog/base.html` — общий layout (сайдбар, меню, футер).
- **Страницы**: главная, каталог, категория, контакты (форма обратной связи и список из БД).
- **Статика**: Bootstrap 5, иконки, `catalog/static/catalog/` (css, js, изображения).

Маршруты: `/` (главная), `/catalog/`, `/category/`, `/category/<id>/`, `/contacts/`. Для продолжения разработки можно ориентироваться на структуру страниц в web_app и дополнять представления и шаблоны в приложении `catalog`.
