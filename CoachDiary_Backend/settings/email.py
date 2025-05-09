import os

from django.conf import settings
from dotenv import load_dotenv

load_dotenv()

if settings.DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND')

EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT'))
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL')

SITE_URL = os.environ.get('SITE_URL')