#consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json, asyncio
from websocket_app.fetch_script import fetch_calls_from_api  # Ajusta el import

class MyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

        # Envía mensaje de bienvenida
        await self.send(text_data=json.dumps({"message": "WebSocket conectado"}))
        await self.send_calls_update()
        self.loop_task = asyncio.create_task(self.periodic_updates())

    async def disconnect(self, code):
        if hasattr(self, 'loop_task'):
            self.loop_task.cancel()

        # Llama a tu API proxy y envía los datos
        # loop = asyncio.get_event_loop()
        # data = await loop.run_in_executor(None, fetch_calls_from_api)
    async def periodic_updates(self):
        while True:
            await asyncio.sleep(5)  # cada 5 segundos
            await self.send_calls_update()

    async def send_calls_update(self):
        data = await asyncio.get_event_loop().run_in_executor(None, fetch_calls_from_api)
        if data:
            await self.send(text_data=json.dumps({
                "type": "callsUpdate",
                "payload": {"getCallsOnHoldData": data}
            }))
