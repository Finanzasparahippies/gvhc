#!/usr/bin/env bash
set -o errexit

# Directorio de instalación dentro del proyecto
INSTALL_DIR="./ffmpeg_bin"
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Descargar y extraer FFmpeg
FFMPEG_URL="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
wget -O ffmpeg.tar.xz "$FFMPEG_URL"
tar xvf ffmpeg.tar.xz

# Copiamos los binarios a la raíz de nuestro directorio de instalación
# El nombre del subdirectorio extraído cambia con la versión, por lo que lo buscamos dinámicamente
FFMPEG_SUBDIR=$(find . -maxdepth 1 -type d -name "ffmpeg-*" -print -quit)
cp "$FFMPEG_SUBDIR/ffmpeg" .
cp "$FFMPEG_SUBDIR/ffprobe" .

# Limpiamos los archivos temporales para reducir el tamaño final de la imagen
rm -r "$FFMPEG_SUBDIR" ffmpeg.tar.xz
cd ..

# Agregamos el directorio de instalación al PATH del sistema para que la app lo encuentre
export PATH="$INSTALL_DIR:$PATH"
echo "PATH del entorno de construcción actualizado: $PATH"

# Continuamos con el resto de la construcción
pip cache purge
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python -m spacy download es_core_news_sm
python manage.py collectstatic --no-input
python manage.py migrate