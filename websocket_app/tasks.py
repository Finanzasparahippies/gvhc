#websocket_app/task.py
from celery import shared_task
from .fetch_script import fetch_calls_on_hold_data, fetch_live_queue_status_data
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import hashlib
import json
from .monitoring import get_resource_metrics
import logging

logger = logging.getLogger(__name__)
_last_checksum = None  # Guardar el último estado
_last_live_queue_status_checksum = None

def get_checksum(data_dict, key):
    # Asegúrate de que el key existe y es una lista para hashing
    data_to_hash = data_dict.get(key, [])
    # Convertir a JSON string, ordenar las claves para hashing consistente
    return hashlib.md5(json.dumps(data_to_hash, sort_keys=True).encode()).hexdigest()

@shared_task
def broadcast_calls_update():
    global _last_calls_checksum, _last_live_queue_status_checksum
    try:
        channel_layer = get_channel_layer()
        if channel_layer is None:
            print("Error: Channel layer not configured.")
            return
        
        payload_from_sharpen = async_to_sync(fetch_calls_on_hold_data)()
        current_checksum = get_checksum(payload_from_sharpen, 'getCallsOnHoldData')

        live_queue_status_payload = async_to_sync(fetch_live_queue_status_data)()
        current_live_queue_status_checksum = get_checksum(live_queue_status_payload, 'liveQueueStatus') # Asumiendo que `fetch_live_queue_status_data` devuelve {'liveQueueStatus': [...]}

        full_frontend_payload = {
            "getCallsOnHoldData": payload_from_sharpen.get('getCallsOnHoldData', []),
            "liveQueueStatus": live_queue_status_payload.get('liveQueueStatus', [])
        }
        if payload_from_sharpen != _last_calls_checksum or current_live_queue_status_checksum != _last_live_queue_status_checksum:
            _last_checksum = current_checksum 
            _last_live_queue_status_checksum = current_live_queue_status_checksum

            async_to_sync(channel_layer.group_send)(
                "calls",
                {
                    "type": "send_calls",
                    "payload": payload_from_sharpen 
                }
            )
            logger.info("[Celery] Datos de llamadas o cola cambiaron, emitido a clientes.")
        else:
            logger.info("[Celery] Sin cambios en llamadas ni cola, no se emitió.")

    except Exception as e:
        logger.error(f"Error en Celery broadcast_all_realtime_updates: {e}", exc_info=True)



@shared_task
def log_system_metrics():
    metrics = get_resource_metrics()
    logger.info(f"[Metrics] RAM: {metrics['memory_used_mb']} MB ({metrics['memory_percent']}%), CPU: {metrics['cpu_percent']}%")
