# Dockerfile para desplegar una aplicación Django con Daphne en Fly.io
FROM python:3.13-slim

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos del proyecto
COPY . /app

# Instalar dependencias
RUN apt-get update
RUN apt-get install -y build-essential libpq-dev
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN rm -rf /root/.cache/pip

# Recolectar archivos estáticos
CMD ["./start.sh"]

# Puerto de Daphne
EXPOSE 8080

# Puedes dejar el CMD vacío aquí porque Fly usará procesos distintos por máquina
# CMD ["daphne", "gvhc.asgi:application", "--port", "8080", "--bind", "0.0.0.0", "-v3"]
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

ENTRYPOINT ["/app/start.sh"]