celery -A gvhc beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
