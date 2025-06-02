import os
from dotenv import load_dotenv

load_dotenv()

CELERY_BROKER_URL = os.environ.get(
    "CELERY_BROKER_URL",
    f"redis://{os.getenv('REDIS_HOST', 'localhost')}:6379/0",
)

CELERY_RESULT_BACKEND = os.environ.get(
    "CELERY_RESULT_BACKEND",
    f"redis://{os.getenv('REDIS_HOST', 'localhost')}:6379/1",
)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'