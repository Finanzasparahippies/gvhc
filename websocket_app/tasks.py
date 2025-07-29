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
_last_checksum = None  # Guardar el último estado
_last_live_queue_status_checksum = None

def get_checksum(data):
    data_to_hash = data.get('getCallsOnHoldData', [])
    return hashlib.md5(json.dumps(data_to_hash, sort_keys=True).encode('utf-8')).hexdigest() # Specify encoding

@shared_task
def broadcast_calls_update():
    global _last_calls_checksum, _last_live_queue_status_checksum
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            logging.error("Error: Channel layer not configured.")
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
            logging.info("[Celery] Datos cambiaron, emitido a clientes.")
        else:
            logging.info("[Celery] Sin cambios, no se emitió.")

    except Exception as e:
        logging.error("Error en Celery broadcast_calls_update:", e)



@shared_task
def log_system_metrics():
    try:
        metrics = get_resource_metrics()
        logger.info(f"[Metrics] RAM: {metrics['memory_used_mb']:.2f} MB ({metrics['memory_percent']:.2f}%), CPU: {metrics['cpu_percent']:.2f}%")
    except Exception as e:
        logger.exception("Error en Celery log_system_metrics:")