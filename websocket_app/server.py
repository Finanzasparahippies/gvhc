# C:\Users\Agent\Documents\Zoom\config\files\gvhc\websocket_app\server.py

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json # Importar json para serializar el mensaje inicial
# Use relative imports (single dot for siblings in the same package)
from .fetch_script import check_for_updates, fetch_calls_from_api
from .utils import active_connections
from .utils import broadcast_new_data
app = FastAPI()

# Permitir conexiones desde tu frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# The 'active_connections' list should ideally be defined *once*
# If it's defined in websocket_utils, you don't need it here.
# Remove this line if it's already in websocket_utils.py:
# active_connections: list[WebSocket] = [] # <-- Potentially remove this line from server.py

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(check_for_updates())

@app.websocket("/ws/calls/") # Fixed typo: changed "ws/calls" to "/ws/calls"
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    print(f"DEBUG WebSocket {websocket.client} accepted by application. Total connections: {len(active_connections)}")
    try:
    # **1. Enviar datos iniciales al cliente recién conectado**
    # Esto asegura que el cliente obtenga el estado actual inmediatamente
        initial_data = fetch_calls_from_api()
        if initial_data:
            await websocket.send_json({
                "type": "callsUpdate",
                "payload": {"getCallsOnHoldData": initial_data, "getCallsOnHoldDescription": "", "getCallsOnHoldStatus": "Complete"}
            })
            print(f"DEBUG Sent initial callsUpdate to new client {websocket.client}")
        else:
            print(f"WARNING No initial data to send to new client {websocket.client}")

        # Mantener la conexión abierta para futuras transmisiones
        while True:
            # Puedes añadir aquí lógica para recibir mensajes del cliente si es necesario,
            # o simplemente mantener el bucle para que la conexión no se cierre.
            # Por ahora, solo esperamos para mantenerla viva.
            await asyncio.sleep(1) # Pequeña pausa para no consumir CPU innecesariamente

    except Exception as e:
        print(f"ERROR WebSocket error in endpoint for client {websocket.client}: {e}")
    finally:
        # Asegurarse de que la conexión se elimine de la lista al desconectarse
        if websocket in active_connections:
            active_connections.remove(websocket)
            print(f"DEBUG WebSocket {websocket.client} disconnected. Remaining connections: {len(active_connections)}")

