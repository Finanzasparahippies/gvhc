#websocket_app/task.py
import logging
import hashlib
import json
from celery import shared_task
from .fetch_script import fetch_calls_on_hold_data, fetch_live_queue_status_data
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)
_last_calls_on_hold_checksum = None
_last_live_queue_status_checksum = None

def get_checksum_for_data(data, key_to_hash):
    data_to_hash = data.get(key_to_hash, [])
    try:
        return hashlib.md5(json.dumps(data_to_hash, sort_keys=True).encode('utf-8')).hexdigest()
    except TypeError as e:
        logger.error(f"Error creating checksum for key '{key_to_hash}': {e}. Data: {data_to_hash}")
        return None # Or raise the error, depending on desired behavior

@shared_task
def broadcast_calls_update():
    global _last_calls_on_hold_checksum, _last_live_queue_status_checksum
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            logging.error("Error: Channel layer not configured.")
            return
        
        calls_on_hold_data  = async_to_sync(fetch_calls_on_hold_data)()
        current_calls_on_hold_checksum = get_checksum_for_data(calls_on_hold_data, 'getCallsOnHoldData')

        live_queue_status_payload = async_to_sync(fetch_live_queue_status_data)()
        current_live_queue_status_checksum = get_checksum_for_data(live_queue_status_payload, 'liveQueueStatus') 

        full_frontend_payload = {
            "getCallsOnHoldData": calls_on_hold_data.get('getCallsOnHoldData', []),
            "liveQueueStatus": live_queue_status_payload.get('liveQueueStatus', [])
        }
        if (current_calls_on_hold_checksum is not None and current_live_queue_status_checksum is not None and
            (current_calls_on_hold_checksum != _last_calls_on_hold_checksum or
            current_live_queue_status_checksum != _last_live_queue_status_checksum)):
            
            _last_calls_on_hold_checksum = current_calls_on_hold_checksum
            _last_live_queue_status_checksum = current_live_queue_status_checksum

            async_to_sync(channel_layer.group_send)(
                "calls",
                {
                    "type": "send_calls",
                    "payload": full_frontend_payload  
                }
            )
            logging.info("[Celery] Datos cambiaron, emitido a clientes.")
        else:
            logging.info("[Celery] Sin cambios, no se emitió.")

    except Exception as e:
        logging.error("Error en Celery broadcast_calls_update:", e)

@shared_task
def log_system_metrics():
    """
    Tarea de Celery para loggear las métricas del sistema.
    Asume que get_resource_metrics() está accesible o se importa correctamente.
    """
    try:
        # Aquí necesitas una forma de obtener las métricas.
        # Si usas la misma lógica que en views.py, podrías hacer algo como:
        import psutil
        memory = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=0.5)
        metrics = {
            "memory_used_mb": round(memory.used / (1024 ** 2), 2),
            "memory_percent": memory.percent,
            "cpu_percent": cpu
        }
        logger.info(f"[Metrics] RAM: {metrics['memory_used_mb']:.2f} MB ({metrics['memory_percent']:.2f}%), CPU: {metrics['cpu_percent']:.2f}%")
    except Exception as e:
        logger.exception("Error en Celery log_system_metrics:")