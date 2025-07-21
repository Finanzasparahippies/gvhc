# consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json
from websocket_app.fetch_script import fetch_calls_from_api  # Ajusta el import
import asyncio

class MyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

        # Envía mensaje de bienvenida
        await self.send(text_data=json.dumps({"message": "WebSocket conectado"}))

        # Llama a tu API proxy y envía los datos
        # loop = asyncio.get_event_loop()
        # data = await loop.run_in_executor(None, fetch_calls_from_api)

        data = await asyncio.get_event_loop().run_in_executor(None, fetch_calls_from_api)
        if data:
            await self.send(text_data=json.dumps({
                "type": "callsUpdate",
                "payload": {"getCallsOnHoldData": data}
            }))
