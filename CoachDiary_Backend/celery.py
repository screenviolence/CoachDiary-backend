import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoachDiary_Backend.settings.settings')

app = Celery('CoachDiary_Backend')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()