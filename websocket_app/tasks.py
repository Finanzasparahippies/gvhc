#websocket_app/task.py
from celery import shared_task
from .fetch_script import fetch_calls_on_hold_data
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import hashlib
import json

_last_checksum = None  # Guardar el último estado


def get_checksum(data):
    return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()

@shared_task
def broadcast_calls_update():
    global _last_checksum
    try:
        channel_layer = get_channel_layer()
        payload = async_to_sync(fetch_calls_on_hold_data)()
        checksum = get_checksum(payload)
        if checksum != _last_checksum:
            _last_checksum = checksum
            async_to_sync(channel_layer.group_send)(
                "calls",
                {
                    "type": "send.calls",
                    "payload": payload
                }
            )
            print("[Celery] Datos cambiaron, emitido a clientes.")
        else:
            print("[Celery] Sin cambios, no se emitió.")

    except Exception as e:
        print("Error en Celery broadcast_calls_update:", e)