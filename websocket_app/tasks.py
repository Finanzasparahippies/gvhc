#websocket_app/task.py
import logging
import hashlib
import json
from celery import shared_task
from .fetch_script import fetch_calls_on_hold_data, fetch_live_queue_status_data
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .fetch_script import fetch_calls_on_hold_data
from .monitoring import get_resource_metrics

logger = logging.getLogger(__name__)

_last_data_checksums = {
    'getCallsOnHoldData': None,
    'liveQueueStatus': None,
    # Puedes añadir más si tu full_frontend_payload crece
}

def get_checksum(data_to_hash):
    """
    Calcula un checksum MD5 para los datos proporcionados.
    Asegura que los datos sean una lista serializable para JSON.
    """
    # Convertir a una lista si no lo es, o asegurar que sea serializable.
    # Si data_to_hash es None, lo convertimos a una lista vacía para que no falle el JSON.
    if data_to_hash is None:
        processed_data = []
    elif not isinstance(data_to_hash, list):
        processed_data = [data_to_hash] # Si es un solo elemento, lo envolvemos en una lista
    else:
        processed_data = data_to_hash # Si ya es una lista, la usamos directamente

    # Usamos sort_keys=True para asegurar un orden consistente para el hashing.
    try:
        return hashlib.md5(json.dumps(processed_data, sort_keys=True).encode('utf-8')).hexdigest()
    except TypeError as e:
        logger.error(f"TypeError al calcular checksum: {e}. Datos problemáticos: {processed_data}")
        # Retorna un checksum único para indicar un error o un estado no válido
        return "error_checksum_" + str(hash(json.dumps(processed_data, sort_keys=True))) # Intenta crear un hash único

@shared_task
def broadcast_calls_update():
    global _last_data_checksums # Importante: indica que vas a modificar esta variable global
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            logging.error("Error: Channel layer not configured.")
            return
        
        payload_on_hold = async_to_sync(fetch_calls_on_hold_data)()
        calls_on_hold_data = payload_on_hold.get('getCallsOnHoldData', []) if isinstance(payload_on_hold, dict) else []
        current_calls_on_hold_checksum = get_checksum(calls_on_hold_data)

        payload_live_queue = async_to_sync(fetch_live_queue_status_data)()
        live_queue_status_data = payload_live_queue.get('liveQueueStatus', []) if isinstance(payload_live_queue, dict) else []
        current_live_queue_status_checksum = get_checksum(live_queue_status_data)

        full_frontend_payload = {
            "getCallsOnHoldData": calls_on_hold_data,
            "getLiveQueueStatusData": live_queue_status_data
        }
        data_changed = False

        if current_calls_on_hold_checksum != _last_data_checksums['getCallsOnHoldData']:
            data_changed = True
            _last_data_checksums['getCallsOnHoldData'] = current_calls_on_hold_checksum
            logger.info("Checksum para 'getCallsOnHoldData' ha cambiado.")

        if current_live_queue_status_checksum != _last_data_checksums['liveQueueStatus']:
            data_changed = True
            _last_data_checksums['liveQueueStatus'] = current_live_queue_status_checksum
            logger.info("Checksum para 'liveQueueStatus' ha cambiado.")

        if data_changed:
            async_to_sync(channel_layer.group_send)(
                "calls",
                {
                    "type": "dataUpdate",
                    "payload": full_frontend_payload
                }
            )
            logger.info("[Celery] Datos cambiaron, emitido a clientes WebSocket.")
        else:
            logger.info("[Celery] Sin cambios en los datos, no se emitió a clientes WebSocket.")

    except Exception as e:
        logger.exception(f"Error en Celery broadcast_calls_update: {e}") # Usar logger.exception para incluir traceback




@shared_task
def log_system_metrics():
    try:
        metrics = get_resource_metrics()
        logger.info(f"[Metrics] RAM: {metrics['memory_used_mb']:.2f} MB ({metrics['memory_percent']:.2f}%), CPU: {metrics['cpu_percent']:.2f}%")
    except Exception as e:
        logger.exception("Error en Celery log_system_metrics:")