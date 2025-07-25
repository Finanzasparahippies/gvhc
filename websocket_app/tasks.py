#websocket_app/task.py
from celery import shared_task
from .fetch_script import fetch_calls_on_hold_data
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import hashlib
import json

_last_checksum = None  # Guardar el último estado


def get_checksum(data):
    data_to_hash = data.get('getCallsOnHoldData', [])
    return hashlib.md5(json.dumps(data_to_hash, sort_keys=True).encode()).hexdigest()

@shared_task
def broadcast_calls_update():
    global _last_checksum
    try:
        channel_layer = get_channel_layer()
        if channel_layer is None:
            print("Error: Channel layer not configured.")
            return
        payload_from_sharpen = async_to_sync(fetch_calls_on_hold_data)()
        current_checksum = get_checksum(payload_from_sharpen)
        if current_checksum  != _last_checksum:
            _last_checksum = current_checksum 
            async_to_sync(channel_layer.group_send)(
                "calls",
                {
                    "type": "send_calls",
                    "payload": payload_from_sharpen 
                }
            )
            print("[Celery] Datos cambiaron, emitido a clientes.")
        else:
            print("[Celery] Sin cambios, no se emitió.")

    except Exception as e:
        print("Error en Celery broadcast_calls_update:", e)
