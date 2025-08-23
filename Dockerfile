# Dockerfile para desplegar una aplicación Django con Daphne en Fly.io
FROM python:3.13-slim

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos del proyecto
COPY . /app

# Instalar dependencias
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libsndfile1 \
 && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN python -m spacy download en_core_web_sm && python -m spacy download es_core_news_sm
RUN rm -rf /root/.cache/pip

RUN chmod +x /app/start.sh

EXPOSE 8080
# Recolectar archivos estáticos
# Puerto de Daphne

# Puedes dejar el CMD vacío aquí porque Fly usará procesos distintos por máquina
# CMD ["daphne", "gvhc.asgi:application", "--port", "8080", "--bind", "0.0.0.0", "-v3"]
ENTRYPOINT ["/app/start.sh"]