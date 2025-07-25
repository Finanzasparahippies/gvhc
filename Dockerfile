# Dockerfile para desplegar una aplicación Django con Daphne en Fly.io
FROM python:3.12-slim

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos del proyecto
COPY . /app

# Instalar dependencias
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && pip install --upgrade pip \
    && pip install -r requirements.txt

# Recolectar archivos estáticos
RUN python manage.py collectstatic --noinput

# Puerto de Daphne
EXPOSE 8080

# Puedes dejar el CMD vacío aquí porque Fly usará procesos distintos por máquina
# CMD ["daphne", "gvhc.asgi:application", "--port", "8080", "--bind", "0.0.0.0", "-v3"]
