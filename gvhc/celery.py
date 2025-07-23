# gvhc/celery.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gvhc.settings')

app = Celery('gvhc')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
