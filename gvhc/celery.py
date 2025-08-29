# gvhc/celery.py
import os
from celery import Celery

import tracemalloc
import atexit

@atexit.register
def display_top():
    print("[Tracemalloc] Top 10 memory allocations:")
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')

    for stat in top_stats[:10]:
        print(stat)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gvhc.settings')

app = Celery('gvhc')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')