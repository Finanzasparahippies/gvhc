#consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json
import asyncio

class MyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("calls", self.channel_name)
        await self.accept()
        print(f"[{self.channel_name}] WebSocket connected.")

        await self.send(text_data=json.dumps({"message": "WebSocket conectado"}))

        # 🔹 Enviar datos iniciales (opcional si ya lo hace el frontend)
        from .fetch_script import fetch_calls_on_hold_data
        initial_data = await fetch_calls_on_hold_data()
        await self.send(text_data=json.dumps({
            "type": "callsUpdate",
            "payload": initial_data
        }))

        # 🔸 Keep connection alive (opcional, puede omitirse si backend o frontend lo hacen)
        self.keepalive_task = asyncio.create_task(self.keep_alive())

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("calls", self.channel_name)
        if hasattr(self, "keepalive_task"):
            self.keepalive_task.cancel()

    async def keep_alive(self):
        try:
            while True:
                await asyncio.sleep(30)  # cada 30 segundos
                await self.send(text_data=json.dumps({"type": "ping"}))
        except asyncio.CancelledError:
            pass

    async def send_calls(self, event):
        print("[Consumer] Enviando llamada a cliente:", event)
        await self.send(text_data=json.dumps({
            "type": "callsUpdate",
            "payload": event.get('payload', {})
        }))