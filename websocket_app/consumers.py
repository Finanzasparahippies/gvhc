#consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json
from .fetch_script import fetch_calls_on_hold_data 
from asgiref.sync import sync_to_async # Import this

class MyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("calls", self.channel_name)
        await self.accept()
        print(f"[{self.channel_name}] WebSocket connected.")

        # Envía mensaje de bienvenida
        await self.send(text_data=json.dumps({"message": "WebSocket conectado"}))
        
        initial_data = await fetch_calls_on_hold_data()
        await self.send(text_data=json.dumps({
            "type": "callsUpdate",
            "payload": initial_data
        }))


    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("calls", self.channel_name)

    # async def periodic_updates(self):
    #     try:
    #         while True:
    #             await self.send_calls_update()
    #             await asyncio.sleep(5)  # Espera 5 segundos entre actualizaciones
    #     except asyncio.CancelledError:
    #         print(f"[{self.channel_name}] Periodic updates task was cancelled.")
    #     except Exception as e:
    #         # Captura cualquier excepción inesperada en el bucle
    #         print(f"[{self.channel_name}] CRITICAL Error in periodic updates loop: {e}. Closing WebSocket.")
    #         await self.close() 

    # async def send_calls_update(self):
    #     try:
    #         # ✅ Esta llamada ahora usa toda la lógica centralizada y es 100% eficiente
    #         data = await fetch_calls_on_hold_data()

    #         await self.send(text_data=json.dumps({
    #             "type": "callsUpdate",
    #             "payload": data
    #         }))
    #     except Exception as e:
    #         print(f"[{self.channel_name}] Unexpected error in send_calls_update: {e}")
    #         # Manejo de errores...
    #         await self.send(text_data=json.dumps({"type": "error", "message": "Unexpected server error."}))

# async def send_calls(self, event):
#     try:
#         payload = event.get("payload", {})
#         await self.send(text_data=json.dumps({
#             "type": "callsUpdate",
#             "payload": payload
#         }))
#     except Exception as e:
#         print(f"[{self.channel_name}] Error in send_calls handler: {e}")
#         await self.send(text_data=json.dumps({"type": "error", "message": "Error broadcasting update."}))

    async def send_calls(self, event):
        await self.send(text_data=json.dumps({
            "type": "callsUpdate",
            "payload": event.get('payload', {})
        }))