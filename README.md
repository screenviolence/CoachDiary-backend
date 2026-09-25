# 📘 Дневник тренера — серверная часть

Серверная часть веб-сервиса **«Дневник тренера»** для учёта спортивной подготовки.  
Проект написан на Python с использованием **Django REST Framework**.

![433079695-dbcb3301-9881-4ced-b3f3-3ef03c6fbb42-round-corners](https://github.com/user-attachments/assets/bf4a6265-dc1b-43cd-b7c5-2a95cc311e03)

Legacy-версия проекта доступна [здесь](https://github.com/screenviolence/coachdiary).

## 🛠️ Стек технологий

- Python 3.12
- Poetry
- Django 5 / Django REST Framework
- PostgreSQL 17
- Redis 7
- Celery
- Gunicorn в production
- Django development server в development
- Docker / Docker Compose

## 📦 Docker-архитектура

Проект использует базовый Compose-файл и отдельные конфигурации для development и production:

```text
docker-compose.yml
├── общие сервисы и настройки
├── db
├── redis
├── web
└── celery_worker

docker-compose.dev.yml
└── development-настройки:
    ├── Django runserver
    ├── hot reload
    ├── bind mount исходников
    └── локальные порты

docker-compose.prod.yml
└── production-настройки:
    ├── Gunicorn
    ├── collectstatic
    ├── production static volume
    └── localhost:8000 для внешнего reverse proxy
```

### Сервисы

| Сервис | Назначение |
|---|---|
| `web` | Django-приложение: API и admin |
| `db` | PostgreSQL |
| `redis` | Брокер сообщений и backend результатов Celery |
| `celery_worker` | Фоновые задачи, включая отправку email |

В production Django публикуется только на `127.0.0.1:8000`; внешний reverse proxy и TLS настраиваются отдельно на хосте.

---

## 🚀 Локальный запуск

### 1. Клонируйте репозиторий

```bash
git clone https://github.com/screenviolence/CoachDiary-backend.git
cd CoachDiary-backend
```

### 2. Создайте `.env`

Создайте файл `.env` в корне проекта:

```dotenv
# Django
DJANGO_SECRET_KEY=dev-secret-key
DJANGO_DEBUG=True
SITE_URL=http://localhost:8000

# PostgreSQL
DB_NAME=coachdiary
DB_USER=coach
DB_PASSWORD=coach_dev_password
DB_HOST=db
DB_PORT=5432

# Redis / Celery
REDIS_HOST=redis
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
```

При `DJANGO_DEBUG=True` Django использует console email backend, поэтому SMTP-настройки для локальной разработки не обязательны.

### 3. Запустите development-окружение

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

В development:

- Django запускается через `runserver`;
- исходники монтируются в `/app`;
- изменения кода подхватываются без пересборки контейнера;
- Django доступен на `127.0.0.1:8000`;
- PostgreSQL доступен на `127.0.0.1:5432`;
- Redis доступен на `127.0.0.1:6379`.

Приложение:

http://127.0.0.1:8000

### 4. Проверьте состояние контейнеров

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml ps
```

### 5. Остановите development-окружение

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml down
```

---

## 🧪 Тестовые данные

Чтобы наполнить базу тестовыми данными:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py create_test_data
```

> ⚠️ Команда спрашивает подтверждение и затем **полностью очищает текущую базу данных** перед созданием тестовых данных.

Тестовые пользователи:

```text
user0@example.com
user1@example.com

password: password
```

---

## 🧰 Полезные development-команды

### Логи Django

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f web
```

### Логи Celery

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f celery_worker
```

### Все основные логи

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f web celery_worker redis
```

### Войти в контейнер Django

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web /bin/bash
```

### Создать суперпользователя

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py createsuperuser
```

### Создать миграции

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py makemigrations
```

### Применить миграции

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py migrate
```

---

## 🌐 Production

В production используются:

```text
docker-compose.yml
docker-compose.prod.yml
```

`docker-compose.prod.yml`:

- запускает Django через Gunicorn;
- выполняет миграции перед стартом;
- выполняет `collectstatic`;
- монтирует `/var/www/coachdiary/static`;
- публикует Django только на `127.0.0.1:8000`.

PostgreSQL и Redis наружу не публикуются.

### 1. Production `.env`

На сервере должен находиться отдельный production `.env`, например:

```dotenv
# Django
DJANGO_SECRET_KEY=your-production-secret
DJANGO_DEBUG=False
SITE_URL=https://coachdiary.ru

# PostgreSQL
DB_NAME=coachdiary
DB_USER=coach
DB_PASSWORD=strong-production-password
DB_HOST=db
DB_PORT=5432

# Redis / Celery
REDIS_HOST=redis
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=465
EMAIL_USE_SSL=True
EMAIL_HOST_USER=do-not-reply@example.com
EMAIL_HOST_PASSWORD=your-smtp-password
DEFAULT_FROM_EMAIL=do-not-reply@example.com
```

### 2. Подготовьте каталог для static

Production Compose монтирует:

```text
/var/www/coachdiary/static
```

в:

```text
/app/CoachDiary_Backend/staticfiles
```

Каталог на хосте должен существовать и быть доступен пользователю контейнера для записи.

### 3. Проверьте production-конфигурацию

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml config
```

Перед запуском убедитесь, что:

- у `web` опубликован только `127.0.0.1:8000`;
- у `db` нет `ports`;
- у `redis` нет `ports`;
- у `web` подключён `/var/www/coachdiary/static`.

### 4. Запустите production

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### 5. Проверьте состояние

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
```

### 6. Остановите production

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml down
```

---

## 🔀 Reverse proxy

Backend в production слушает только:

```text
127.0.0.1:8000
```

Внешний reverse proxy и TLS настраиваются отдельно на production-хосте.

Статические файлы Django находятся на хосте в:

```text
/var/www/coachdiary/static
```

Конфигурация reverse proxy хранится и обслуживается отдельно от Docker Compose этого репозитория.

---

## ✉️ Email и Celery

Email отправляется асинхронно:

```text
Django → Redis → Celery worker → SMTP
```

Поэтому при проблемах с отправкой почты в production в первую очередь смотрите логи `celery_worker`:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f --tail=200 celery_worker
```

Проверить, отвечает ли Celery:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec celery_worker celery -A CoachDiary_Backend inspect ping
```

Проверить зарегистрированные задачи:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec celery_worker celery -A CoachDiary_Backend inspect registered
```

Логи Django, Celery и Redis одновременно:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f --tail=200 web celery_worker redis
```

---

## 📖 API-документация

API-схема генерируется с помощью `drf-spectacular`.

В debug-режиме Swagger UI доступен по адресу:

http://127.0.0.1:8000/api/docs/
