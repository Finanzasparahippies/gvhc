@echo off
echo --- INICIO DE PRUEBA DE DIAGNOSTICO ---
echo.

set "FFMPEG_PATH=D:\GVHC\09-gvhc\gvhc\env\ffmpeg\bin"
echo Paso 1: La ruta de FFmpeg se ha definido como:
echo "%FFMPEG_PATH%"
echo.
pause

set "PATH=%FFMPEG_PATH%;%PATH%"
echo Paso 2: El PATH temporal de esta ventana ahora es:
echo "%PATH%"
echo (Se puede ver que la ruta de FFmpeg esta al principio)
echo.
pause

echo Paso 3: A continuacion, se intentara ejecutar "ffmpeg -version".
echo Presta mucha atencion al error EXACTO que aparecera.
echo.
pause

REM --- La linea clave: Sin ">nul 2>&1" para poder ver el error ---
ffmpeg -version

echo.
echo --- FIN DE PRUEBA ---
echo.
echo El error que viste justo arriba es la verdadera causa del problema.
pause