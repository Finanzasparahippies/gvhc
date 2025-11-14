@echo off
setlocal enabledelayedexpansion
REM --- run_websocket.bat ---

REM Establece la ruta de ffmpeg para esta sesión de terminal.
set "FFMPEG_PATH=D:\GVHC\GVHC\Call_analizer_setting_files\ffmpeg-8.0-full_build\ffmpeg-8.0-full_build\bin"

echo.
echo --- Verificando FFmpeg ---
echo Buscando en: !FFMPEG_PATH!
echo.

REM Verifica que el ejecutable exista
if not exist "!FFMPEG_PATH!\ffmpeg.exe" (
    echo ❌ ERROR: No se encontró "!FFMPEG_PATH!\ffmpeg.exe".
    echo Verifique la ruta.
    pause
    exit /b 1
)

echo ✅ FFmpeg encontrado.
echo.

REM Inicia el servidor de Daphne.
echo Iniciando el servidor WebSocket con Daphne...
echo.
python -m daphne gvhc.asgi:application --port 8001 --bind 0.0.0.0