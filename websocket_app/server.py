# C:\Users\Agent\Documents\Zoom\config\files\gvhc\websocket_app\server.py

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import asyncio

# Use relative imports (single dot for siblings in the same package)
from .fetch_script import check_for_updates
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

@app.websocket("/ws/calls") # Fixed typo: changed "ws/calls" to "/ws/calls"
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await asyncio.sleep(1)
    except Exception as e: # Capture the exception here for the print statement
        print(f"WebSocket error in endpoint: {e}")
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)