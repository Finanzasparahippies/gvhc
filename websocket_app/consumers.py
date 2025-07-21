# yourapp/consumers.py

from channels.generic.websocket import AsyncWebsocketConsumer
import json
import asyncio
from websocket_app.fetch_script import fetch_calls_from_api  # ajusta la ruta

class MyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send(text_data=json.dumps({"message": "WebSocket conectado"}))

        data = await asyncio.get_event_loop().run_in_executor(None, fetch_calls_from_api)
        if data:
            await self.send(text_data=json.dumps({
                "type": "callsUpdate",
                "payload": {"getCallsOnHoldData": data}
            }))

        # Envía actualizaciones cada 5 segundos
        asyncio.create_task(self.periodic_updates())

    async def periodic_updates(self):
        while True:
            data = await asyncio.get_event_loop().run_in_executor(None, fetch_calls_from_api)
            if data:
                await self.send(text_data=json.dumps({
                    "type": "callsUpdate",
                    "payload": {"getCallsOnHoldData": data}
                }))
            await asyncio.sleep(5)