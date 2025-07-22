import os
import redis
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / '.env', override=True)

redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/')
print(f"Intentando conectar a Redis en: {redis_url}")

try:
    # Crea una instancia del cliente Redis
    # decode_responses=True asegura que las respuestas de Redis sean strings de Python
    r = redis.from_url(redis_url, decode_responses=True)

    # Intenta hacer un ping al servidor Redis
    response = r.ping()
    if response:
        print("¡Conexión a Redis exitosa! Ping respondió con:", response)
        # Opcional: Establecer y obtener una clave para verificar escritura/lectura
        r.set('test_key', 'Hello Redis!')
        value = r.get('test_key')
        print(f"Clave 'test_key' establecida y leída: {value}")
        r.delete('test_key') # Limpiar
    else:
        print("Conexión a Redis establecida, pero el ping falló.")

except redis.exceptions.ConnectionError as e:
    print(f"ERROR: No se pudo conectar a Redis. Detalles: {e}")
    print("Por favor, verifica que el servidor Redis esté corriendo y accesible en la URL proporcionada.")
except Exception as e:
    print(f"Ocurrió un error inesperado: {e}")