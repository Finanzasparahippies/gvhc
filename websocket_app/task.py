#websocket_app/task.py
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .fetch_script import fetch_calls_on_hold_data

async def broadcast_calls_update():
    channel_layer = get_channel_layer()
    payload = await fetch_calls_on_hold_data()

    await channel_layer.group_send("calls", {
        "type": "send.calls",
        "payload": payload
    })
