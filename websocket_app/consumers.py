#consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json, asyncio
from .fetch_script import fetch_calls_on_hold_data # 👈 Importa la nueva función

class MyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        print(f"[{self.channel_name}] WebSocket connected.")

        # Envía mensaje de bienvenida
        await self.send(text_data=json.dumps({"message": "WebSocket conectado"}))
        self.loop_task = asyncio.create_task(self.periodic_updates())


    async def disconnect(self, close_code):
        print(f"[{self.channel_name}] WebSocket disconnected with code: {close_code}")
        if hasattr(self, 'loop_task') and not self.loop_task.done():
            self.loop_task.cancel()
            try:
                await asyncio.wait_for(self.loop_task, timeout=2.0)
                print(f"[{self.channel_name}] Periodic updates task cancelled gracefully.")
            except asyncio.CancelledError:
                print(f"[{self.channel_name}] Periodic updates task was already cancelled during wait.")
            except asyncio.TimeoutError:
                print(f"[{self.channel_name}] WARNING: Periodic updates task did not terminate within timeout.")
            except Exception as e:
                print(f"[{self.channel_name}] Error during task cancellation wait: {e}")
        print(f"[{self.channel_name}] Disconnect routine finished.")

    async def periodic_updates(self):
        try:
            while True:
                await self.send_calls_update()
                await asyncio.sleep(5)  # Espera 5 segundos entre actualizaciones
        except asyncio.CancelledError:
            print(f"[{self.channel_name}] Periodic updates task was cancelled.")
        except Exception as e:
            # Captura cualquier excepción inesperada en el bucle
            print(f"[{self.channel_name}] CRITICAL Error in periodic updates loop: {e}. Closing WebSocket.")
            await self.close() 

    async def send_calls_update(self):
        try:
            # ✅ Esta llamada ahora usa toda la lógica centralizada y es 100% eficiente
            data = await fetch_calls_on_hold_data()

            await self.send(text_data=json.dumps({
                "type": "callsUpdate",
                "payload": data
            }))
        except Exception as e:
            print(f"[{self.channel_name}] Unexpected error in send_calls_update: {e}")
            # Manejo de errores...
            await self.send(text_data=json.dumps({"type": "error", "message": "Unexpected server error."}))
