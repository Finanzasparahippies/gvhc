#!/bin/bash

# Iniciar daphne en segundo plano
daphne gvhc.asgi:application --port $PORT --bind 0.0.0.0 -v3 &

# Iniciar celery worker en segundo plano
celery -A gvhc worker --loglevel=info --pool=solo &

# Iniciar celery beat en primer plano (para mantener el contenedor activo)
celery -A gvhc beat --loglevel=info
