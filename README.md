# 📘 Дневник тренера – серверная часть

Привет! 👋  
Это мой учебный проект — серверная часть приложения **"Дневник тренера"**, онлайн-сервиса для учёта спортивной подготовки, написанная на Python с использованием **Django** и **Django REST Framework**.

![433079695-dbcb3301-9881-4ced-b3f3-3ef03c6fbb42-round-corners](https://github.com/user-attachments/assets/bf4a6265-dc1b-43cd-b7c5-2a95cc311e03)

## 🛠️ Стек технологий

- Python 3
- Django
- Django REST Framework
- PostgreSQL

## 🚀 Запуск проекта локально

Для запуска следуйте инструкции ниже.

### 1. Клонируйте репозиторий и перейдите в директорию проекта:

```
git clone https://github.com/screenviolence/CoachDiary-backend.git
cd CoachDiary-backend
```
### 2. Создайте файл .env в корне проекта с переменными окружения:
⚠️ **Проект использует PostgreSQL! Убедитесь, что PostgreSQL установлен, база данных создана и доступна по указанным данным.**
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

# Настройки электронной почты (при запуске с DJANGO_DEBUG=True не требуются, письма выводятся в консоль)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=ваш_хост_smtp
EMAIL_PORT=ваш_порт_smtp
EMAIL_USE_SSL=True
EMAIL_HOST_USER=ваш_пользователь_почты
EMAIL_HOST_PASSWORD=пароль_пользователя_почты
DEFAULT_FROM_EMAIL=адрес_почты_рассылки_по_умолчанию

# Общие настройки сайта (можно оставить пустым)
SITE_URL=https://example.com
```


### 3. Установите менеджер зависимостей Poetry через pip:
```
pip install poetry
```
И затем воспользуйтесь [официальной инструкцией по установке Poetry в систему и добавлению в PATH](https://python-poetry.org/docs/#installing-with-the-official-installer).

### 4. Установите зависимости и активируйте виртуальное окружение:
```
poetry install
eval $(poetry env activate) # Если используется Unix-система
Invoke-Expression (poetry env activate) # Если ОС - Windows
```
### 5. Выполните миграции:
```
python manage.py makemigrations
python manage.py migrate
```
### 6. (необязательно) Используйте создание тестовых данных:
Введите в консоль
```
python manage.py create_test_data
```
и согласитесь.
Команда наполнит базу данных тестовыми данными, чтобы оценить возможности приложения!

### 7. Запустите сервер разработки Django:
```
python manage.py runserver
```

Теперь проект доступен по адресу: http://127.0.0.1:8000

## 📖 Документация API
Документация генерируется автоматически, используя библиотеку drf-spectacular. 

В дебаг-режиме она будет доступна сразу после запуска по адресу: http://127.0.0.1:8000/api/docs/
