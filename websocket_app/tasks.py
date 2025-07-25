#websocket_app/task.py
from celery import shared_task
from .fetch_script import fetch_calls_on_hold_data
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import hashlib
import json
from django.conf import settings # Para acceder a las configuraciones de Redis

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
                    "type": "send_calls",
                    "payload": payload
                }
            )
            print("[Celery] Datos cambiaron, emitido a clientes.")
        else:
            print("[Celery] Sin cambios, no se emitió.")

    except Exception as e:
        print("Error en Celery broadcast_calls_update:", e)

@shared_task
def send_calls_on_hold_to_websocket():
    """
    Celery task to fetch calls on hold data and send it to all connected
    WebSocket clients in the 'calls' group.
    """
    channel_layer = get_channel_layer()
    if channel_layer is None:
        print("Error: Channel layer not configured.")
        return

    # Call the async function from fetch_script using asyncio.run
    # or better, use async_to_sync if this task is not an async task itself.
    # Since shared_task is synchronous by default, async_to_sync is preferred.
    try:
        calls_data = async_to_sync(fetch_calls_on_hold_data)()
        print(f"Fetched calls data for WebSocket: {len(calls_data)} items")

        # Send data to the 'calls' group
        async_to_sync(channel_layer.group_send)(
            "calls",
            {
                "type": "send_calls", # This refers to the send_calls method in MyConsumer
                "payload": calls_data
            }
        )
        print("Calls data sent to WebSocket group.")
    except Exception as e:
        print(f"Error in send_calls_on_hold_to_websocket task: {e}")