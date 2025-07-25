#websocket_app/task.py
from celery import shared_task
from .fetch_script import fetch_calls_on_hold_data
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import hashlib
import json
from django.conf import settings # Para acceder a las configuraciones de Redis
import redis # Importar la librería redis

try:
    _redis_client = redis.from_url(settings.CELERY_BROKER_URL) # Reutiliza la URL del broker si está en Redis
    # O si tienes una URL específica para caching:
    # _redis_client = redis.from_url(settings.REDIS_CACHE_URL)
except Exception as e:
    print(f"Advertencia: No se pudo conectar a Redis para el checksum. El caching de checksum no funcionará. Error: {e}")
    _redis_client = None # Si Redis no está disponible, la lógica de checksum se deshabilitará efectivamente

CHECKSUM_KEY = "last_calls_payload_checksum"

def get_checksum(data):
    """Genera un checksum MD5 del JSON de los datos, ordenando las claves para consistencia."""
    # Asegúrate de que los datos sean siempre un JSON válido y ordenado para un checksum consistente
    return hashlib.md5(json.dumps(data, sort_keys=True).encode('utf-8')).hexdigest()

@shared_task
def broadcast_calls_update():
    """
    Celery task para obtener datos de llamadas en espera y enviarlos a los clientes WebSocket,
    solo si los datos han cambiado desde la última emisión.
    """
    if _redis_client is None:
        print("[Celery] Redis no está configurado o conectado. Saltando verificación de checksum y emitiendo siempre.")
        # En un escenario donde Redis es crítico, quizás quieras lanzar una excepción o notificar.
        # Por ahora, simplemente emitiremos los datos sin verificación si Redis falla.
        # Considera cómo quieres manejar esto en producción.
        force_send = True
    else:
        force_send = False


    try:
        channel_layer = get_channel_layer()
        if channel_layer is None:
            print("Error: Channel layer no configurado.")
            return

        # 1. Obtener los datos más recientes
        payload = async_to_sync(fetch_calls_on_hold_data)()
        
        # Asegúrate de que el payload sea siempre una lista si no hay datos
        if not isinstance(payload, list):
            # Asume que si fetch_calls_on_hold_data no devuelve una lista, es un error o un objeto
            # y queremos que siempre sea una lista para el consumidor.
            # Puedes ajustar esto si fetch_calls_on_hold_data puede devolver un dict con "getCallsOnHoldData"
            # como lo hace tu fetch_script.py al final.
            if isinstance(payload, dict) and "getCallsOnHoldData" in payload and isinstance(payload["getCallsOnHoldData"], list):
                current_calls_data = payload["getCallsOnHoldData"]
            else:
                print(f"Advertencia: fetch_calls_on_hold_data devolvió un formato inesperado: {type(payload)}. Usando lista vacía.")
                current_calls_data = [] # Fallback a lista vacía para evitar errores
        else:
            current_calls_data = payload


        current_checksum = get_checksum(current_calls_data) # Genera checksum de la lista

        last_checksum_from_redis = None
        if _redis_client:
            last_checksum_from_redis = _redis_client.get(CHECKSUM_KEY)
            if last_checksum_from_redis:
                last_checksum_from_redis = last_checksum_from_redis.decode('utf-8')

        if force_send or current_checksum != last_checksum_from_redis:
            # Los datos han cambiado o Redis no está disponible para verificar
            async_to_sync(channel_layer.group_send)(
                "calls",
                {
                    "type": "send_calls",
                    "payload": current_calls_data # Envía la lista de llamadas directamente
                }
            )
            if _redis_client:
                _redis_client.set(CHECKSUM_KEY, current_checksum) # Almacena el nuevo checksum en Redis
            print("[Celery] Datos cambiaron o se forzó el envío, emitido a clientes.")
        else:
            print("[Celery] Sin cambios en los datos, no se emitió.")

    except Exception as e:
        print(f"Error en Celery broadcast_calls_update: {e}")