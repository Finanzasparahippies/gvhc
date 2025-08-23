@echo off
set "PATH=%PATH%;D:\GVHC\ffmpeg-7.1.1-essentials_build\bin"
echo PATH del entorno de desarrollo actualizado para WebSocket: %PATH%
echo Iniciando el servidor WebSocket con Daphne...
python -m daphne gvhc.asgi:application --port 8001 --bind 0.0.0.0