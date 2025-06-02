# 📘 Дневник тренера – серверная часть

Привет! 👋  
Меня зовут Матвей, и это мой учебный проект — серверная часть приложения **"Дневник тренера"**, веб-сервиса для учёта спортивной подготовки, написанная на Python с использованием **Django REST Framework**.

![433079695-dbcb3301-9881-4ced-b3f3-3ef03c6fbb42-round-corners](https://github.com/user-attachments/assets/bf4a6265-dc1b-43cd-b7c5-2a95cc311e03)

## 🛠️ Стек технологий

- Python 3
- Django
- Django REST Framework
- PostgreSQL
- Docker
- Redis
- Celery

## 🚀 Запуск проекта локально

Для запуска следуйте инструкции ниже.

### 1. Клонируйте репозиторий и перейдите в директорию проекта:

```
git clone https://github.com/screenviolence/CoachDiary-backend.git
cd CoachDiary-backend
```
### 2. Создайте файл .env в корне проекта с переменными окружения:
```
# Настройки Django
DJANGO_SECRET_KEY=ваш_секретный_ключ
DJANGO_DEBUG=True

# Настройки базы данных
DB_NAME=имя_вашей_базы_данных
DB_USER=имя_пользователя
DB_PASSWORD=пароль_пользователя
DB_HOST=127.0.0.1
DB_PORT=5432

# Настройки электронной почты
# (при запуске с DEBUG=True не требуются, письма выводятся в консоль)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=ваш_хост_smtp
EMAIL_PORT=ваш_порт_smtp
EMAIL_USE_SSL=True
EMAIL_HOST_USER=ваш_пользователь_почты
EMAIL_HOST_PASSWORD=пароль_пользователя_почты
DEFAULT_FROM_EMAIL=адрес_почты_рассылки_по_умолчанию

# Настройки Redis
REDIS_HOST=redis

# Настройки Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1

# Общие настройки сайта (можно оставить пустым)
SITE_URL=https://example.com
```

### 3. Запустите контейнеры с помощью Docker Сompose:
```
docker-compose up -d
```
Это создаст и запустит контейнеры для базы данных PostgreSQL, Redis и самого Django-приложения.

Теперь проект будет доступен по адресу: http://127.0.0.1:8000

### 4. Создание тестовых данных (опционально):
```
docker-compose exec web python manage.py create_test_data
```
и согласитесь. Выполнение команды может занять некоторое время, в зависимости от производительности вашего компьютера.

Он наполнит базу данных тестовыми данными, чтобы оценить возможности приложения!

### 5. Вход в контейнер:
При необходимости вы можете войти в контейнер с приложением для выполнения команд Django или других задач.
```
# Вход в bash/sh оболочку контейнера
docker-compose exec web /bin/bash

# Посмотреть логи
docker-compose logs -f web
```

## 📖 Документация API
Документация генерируется автоматически, используя библиотеку drf-spectacular. 

В debug-режиме она будет доступна сразу после запуска по адресу: http://127.0.0.1:8000/api/docs/
