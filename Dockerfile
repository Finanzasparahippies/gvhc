# Dockerfile para desplegar una aplicación Django con Daphne en Fly.io
FROM python:3.13-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libsndfile1 \
    ffmpeg \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt
# Descargar modelos de spaCy
RUN python -m spacy download en_core_web_md && python -m spacy download es_core_news_md
RUN rm -rf /root/.cache/pip

# Copiar archivos del proyecto
COPY . /app

RUN chmod +x /app/start.sh

EXPOSE 8080
# Recolectar archivos estáticos
# Puerto de Daphne

# Puedes dejar el CMD vacío aquí porque Fly usará procesos distintos por máquina
# CMD ["daphne", "gvhc.asgi:application", "--port", "8080", "--bind", "0.0.0.0", "-v3"]
ENTRYPOINT ["/app/start.sh"]