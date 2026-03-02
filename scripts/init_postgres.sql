-- Создание базы данных и пользователя для django-orm
-- Запуск: psql -d postgres -f scripts/init_postgres.sql
-- (на macOS часто: текущий пользователь; при необходимости: psql -U postgres -d postgres -f ...)

-- Пользователь (при необходимости смените имя и пароль)
CREATE USER django_orm_user WITH PASSWORD 'django_orm_password';

-- База данных (ENCODING UTF8; локаль по умолчанию сервера)
CREATE DATABASE django_orm
    OWNER django_orm_user
    ENCODING 'UTF8'
    TEMPLATE template0;

-- Подключение к новой БД нужно выполнить отдельно, затем:
\c django_orm

-- Права (на случай если владелец не совпадает с подключающимся пользователем)
GRANT ALL PRIVILEGES ON DATABASE django_orm TO django_orm_user;
GRANT ALL ON SCHEMA public TO django_orm_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO django_orm_user;
