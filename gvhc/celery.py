# gvhc/celery.py
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gvhc.settings')

app = Celery('gvhc')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
app.conf.beat_scheduler = 'django_celery_beat.schedulers.DatabaseScheduler'
app.conf.beat_schedule_filename = os.getenv('CELERY_BEAT_SCHEDULE_FILENAME', '/data/celerybeat-schedule')
app.conf.beat_schedule.update({
    'log-system-metrics-every-5-mins': {
        'task': 'myapp.tasks.log_system_metrics',
        'schedule': crontab(minute='*/5'),
    },
})

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')