# gvhc/celery.py
import os
from celery import Celery
from celery.beat import PersistentScheduler

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gvhc.settings')

app = Celery('gvhc')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
app.conf.beat_scheduler = 'django_celery_beat.schedulers.DatabaseScheduler'
app.conf.beat_schedule_filename = os.getenv('CELERY_BEAT_SCHEDULE_FILENAME', '/data/celerybeat-schedule')

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')