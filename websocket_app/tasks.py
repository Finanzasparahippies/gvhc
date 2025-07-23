#websocket_app/task.py
from celery import shared_task
from .fetch_script import fetch_calls_on_hold_data
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


@shared_task
def broadcast_calls_update():
    print("Iniciando tarea broadcast_calls_update")
    try:
        channel_layer = get_channel_layer()
        print("Obtuve channel_layer")

        payload = async_to_sync(fetch_calls_on_hold_data)()
        print("Obtuve payload:", payload)

        async_to_sync(channel_layer.group_send)(
            "calls",
            {
                "type": "send.calls",
                "payload": payload
            }
        )
        print("Mensaje enviado al grupo")
    except Exception as e:
        print("Error durante ejecución del task:", e)