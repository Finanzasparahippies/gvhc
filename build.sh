#!/usr/bin/env bash
# Exit script if any command fails
set -o errexit

apt-get update
apt-get install -y ffmpeg

python -m pip install --upgrade pip
# Instalar dependencias de Python
pip install -r requirements.txt

# Descargar el modelo de spaCy necesario
python -m spacy download en_core_web_md
python -m spacy download es_core_news_md

# Ejecutar migraciones y otros comandos de despliegue
python manage.py collectstatic --no-input
python manage.py migrate