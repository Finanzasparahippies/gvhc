@echo off
REM --- run_websocket.bat ---

REM Establece la ruta de ffmpeg para esta sesión de terminal.
set "FFMPEG_PATH=D:\GVHC\09-gvhc\gvhc\env\ffmpeg\bin"

REM Elimina la ruta anterior de FFmpeg para evitar conflictos.
set "PATH=%PATH:D:\GVHC\ffmpeg-7.1.1-essentials_build\bin=%"

REM Agrega la nueva ruta de FFmpeg al PATH.
set "PATH=%FFMPEG_PATH%;%PATH%"

echo.
echo --- Verificando FFmpeg ---
echo PATH que se utilizara: %PATH%
echo.

ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ERROR: No se pudo encontrar FFmpeg.
    echo Verifique que la ruta "%FFMPEG_PATH%" sea correcta y contenga ffmpeg.exe.
    echo.
    pause
    exit /b 1
)

echo ✅ FFmpeg encontrado.
echo.

REM Inicia el servidor de Daphne.
echo Iniciando el servidor WebSocket con Daphne...
echo.
python -m daphne gvhc.asgi:application --port 8001 --bind 0.0.0.0