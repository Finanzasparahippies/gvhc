#!/usr/bin/env bash
set -o errexit

# (Si necesitas ffmpeg localmente, puedes incluir los pasos como en tu otro script)

pip install --upgrade pip
pip install -r requirements.txt

# Instalar modelos spaCy
python -m spacy download en_core_web_sm
python -m spacy download es_core_news_sm

python manage.py collectstatic --no-input
python manage.py migrate
