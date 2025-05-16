from django.conf import settings

CORS_ALLOWED_ORIGINS = ["https://coachdiary.ru", "http://127.0.0.1:8000"]
CORS_ALLOW_CREDENTIALS = True

if settings.DEBUG:
    SECURE_SSL_REDIRECT = False
else:
    SECURE_SSL_REDIRECT = True