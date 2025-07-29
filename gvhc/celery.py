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
    'broadcast-all-realtime-updates-every-15-seconds': {
        'task': 'websocket_app.task.broadcast_calls_update', # Asegúrate que la ruta sea correcta
        'schedule': 15.0, # Cada 15 segundos
    },
    'log-system-metrics-every-5-mins': {
        'task': 'gvhc.tasks.log_system_metrics',
        'schedule': crontab(minute='*/5'),
    },
})

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')