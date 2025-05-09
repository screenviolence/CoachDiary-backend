from django.conf import settings
from datetime import timedelta

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication'
    ],
    'EXCEPTION_HANDLER': (
        'CoachDiary_Backend.api.utils.exception_handler.custom_exception_handler'
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=7),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': settings.SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

OAUTH2_PROVIDER = {
    'SCOPES': {'read': 'Read scope',
               'write': 'Write scope',
               },
    'ACCESS_TOKEN_EXPIRE_SECONDS': 604800,
    'REFRESH_TOKEN_EXPIRE_SECONDS': 30 * 24 * 60 * 60,
    'ROTATE_REFRESH_TOKEN': True,
}

SPECTACULAR_SETTINGS = {
    "SCHEMA_PATH_PREFIX": r"/api/"
}