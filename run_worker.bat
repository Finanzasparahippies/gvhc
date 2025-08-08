@echo off
set "PATH=%PATH%;D:\GVHC\ffmpeg-7.1.1-essentials_build\bin"
echo PATH del entorno de desarrollo actualizado para Celery: %PATH%
python -m celery -A gvhc worker --pool=solo --loglevel=info