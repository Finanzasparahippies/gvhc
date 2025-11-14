@echo off
set "PATH=%PATH%;D:\GVHC\ffmpeg-7.1.1-essentials_build\bin"
echo PATH del entorno de desarrollo actualizado para Celery: %PATH%
set TZ=UTC && python -m celery -A gvhc worker -l info -Q default --pool=solo 
  
