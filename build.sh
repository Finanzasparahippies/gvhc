#!/usr/bin/env bash
set -o errexit

# Directorio para la instalación
mkdir -p /opt/render/project/src/ffmpeg_bin
cd /opt/render/project/src/ffmpeg_bin

# URL de descarga de FFmpeg para Linux
FFMPEG_URL="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
wget -O ffmpeg.tar.xz "$FFMPEG_URL"
tar xvf ffmpeg.tar.xz

# El directorio extraído tendrá un nombre como "ffmpeg-N.N-amd64-static"
# Buscamos el directorio y extraemos el binario
FFMPEG_DIR=$(find . -maxdepth 1 -type d -name "ffmpeg-*" -print -quit)
cp "$FFMPEG_DIR/ffmpeg" /usr/local/bin/
cp "$FFMPEG_DIR/ffprobe" /usr/local/bin/

# Limpiamos los archivos descargados
rm -r "$FFMPEG_DIR" ffmpeg.tar.xz

# Continuamos con el resto de la construcción
pip install -r requirements.txt
python -m spacy download en_core_web_md
python -m spacy download es_core_web_md
python manage.py collectstatic --no-input
python manage.py migrate