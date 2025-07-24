web: daphne gvhc.asgi:application --port $PORT --bind 0.0.0.0 -v3
worker: celery -A gvhc worker --loglevel=info --pool=solo
beat: celery -A gvhc beat --loglevel=info