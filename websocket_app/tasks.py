#websocket_app/task.py
from celery import shared_task
from .fetch_script import fetch_calls_on_hold_data
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


@shared_task
def broadcast_calls_update():
    channel_layer = get_channel_layer()
    payload = async_to_sync(fetch_calls_on_hold_data)()
    async_to_sync(channel_layer.group_send)(
        "calls",
        {
            "type": "send.calls",
            "payload": payload
        }
    )