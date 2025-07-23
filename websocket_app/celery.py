# websocket_app/celery.py

import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gvhc.settings")  # ajusta si tu settings se llama distinto

app = Celery("websocket_app")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
