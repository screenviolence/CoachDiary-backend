# 📘 Дневник тренера – серверная часть

Привет! 👋  
Это мой учебный проект — серверная часть приложения **"Дневник тренера"**, написанная на Python с использованием **Django** и **Django REST Framework**.


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
## 2. Создайте файл .env в корне проекта с переменными окружения:
```
DJANGO_SECRET_KEY=ваш_секретный_ключ
DJANGO_DEBUG=True

DB_NAME=имя_вашей_базы_данных
DB_USER=имя_пользователя
DB_PASSWORD=пароль_пользователя
DB_HOST=127.0.0.1
DB_PORT=5432
```
⚠️ Проект использует PostgreSQL, убедитесь, что база данных установлена и доступна по указанным данным.

3. Установите менеджер зависимостей Poetry:
```
pip install poetry
```
Или воспользуйтесь [официальной инструкцией](https://python-poetry.org/docs/).

4. Установите зависимости и активируйте виртуальное окружение:
```
poetry install
Invoke-Expression (poetry env activate)
```
5. Выполните миграции:
```
python manage.py makemigrations
python manage.py migrate
```

6. Запустите сервер разработки Django:
```
python manage.py runserver
```

Теперь проект доступен по адресу: http://127.0.0.1:8000

## 📖 Документация API
Документация выполненена автоматически, используя библиотеку drf-spectacular. 

Она будет доступна после запуска по адресу: http://127.0.0.1:8000/api/docs/
