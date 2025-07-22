#consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json, asyncio
import httpx # Usaremos httpx para llamadas HTTP asíncronas
from websocket_app.fetch_script import fetch_calls_from_api  # Ajusta el import

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
        client = None 
        response = None # Inicializar response para el JSONDecodeError

        try:
            # *** CAMBIO CLAVE: Usar httpx para llamadas HTTP asíncronas ***
            # Esto evita bloquear el event loop con requests.post (que es síncrono)
            # y es más apropiado para Django Channels (basado en ASGI).
            client = httpx.AsyncClient()
            DJANGO_PROXY_URL = "https://gvhc-backend.onrender.com/api/dashboards/proxy/generic/"
            proxy_payload = {
                "endpoint": "V2/queues/getCallsOnHold/",
                "payload": {}
            }
            response = await client.post(DJANGO_PROXY_URL, json=proxy_payload, timeout=10.0) # Añadir timeout
            response.raise_for_status() # Lanza excepción para códigos de estado HTTP 4xx/5xx
            data = response.json()
            print(f"[{self.channel_name}] Data from proxy: {json.dumps(data)}") # Debug print

            if data:
                await self.send(text_data=json.dumps({
                    "type": "callsUpdate",
                    "payload": data
                }))
                print(f"[{self.channel_name}] Sent calls update.")
            else:
                print(f"[{self.channel_name}] No data received from proxy. Sending empty array.")
                await self.send(text_data=json.dumps({
                    "type": "callsUpdate",
                    "payload": {"getCallsOnHoldData": []}
                }))
        except httpx.RequestError as e:
            print(f"[{self.channel_name}] HTTPX Request Error during fetch: {e}")
            await self.send(text_data=json.dumps({"type": "error", "message": f"API fetch error: {e}. Retrying soon."}))
            # Considera si quieres cerrar la conexión o solo registrar el error
        except httpx.HTTPStatusError as e:
            print(f"[{self.channel_name}] HTTP Status Error from proxy: {e.response.status_code} - {e.response.text}")
            await self.send(text_data=json.dumps({"type": "error", "message": f"Proxy HTTP error: {e.response.status_code}. Retrying soon."}))
        except json.JSONDecodeError as e:
            print(f"[{self.channel_name}] JSON Decode Error: {e} - Response: {response.text}")
            await self.send(text_data=json.dumps({"type": "error", "message": "Invalid JSON from API."}))
        except Exception as e:
            print(f"[{self.channel_name}] Unexpected error in send_calls_update: {e}")
            await self.send(text_data=json.dumps({"type": "error", "message": f"Unexpected server error in update: {e}. Retrying soon."}))
        finally:
            if client:
                await client.aclose()
