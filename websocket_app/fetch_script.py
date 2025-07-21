# C:\Users\Agent\Documents\Zoom\config\files\gvhc\websocket_app\fetch_script.py

import asyncio
import requests
import json
# Use relative import (single dot for siblings in the same package)
from .utils import broadcast_new_data

DJANGO_PROXY_URL = "http://localhost:8000/api/dashboards/proxy/generic/" 

def fetch_calls_from_api():
    # ... (rest of the function, no changes here) ...
    try:
        proxy_payload = {
            "endpoint": "V2/queues/getCallsOnHold/",
            "payload": {}
        }
        response = requests.post(DJANGO_PROXY_URL , json=proxy_payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener datos de Django API a través del proxy: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response content: {e.response.text}")
        return None

async def check_for_updates():
    # ... (rest of the function, no changes here) ...
    prev_data = None
    while True:
        print("Buscando actualizaciones de llamadas...")
        new_data = fetch_calls_from_api()
        
        if new_data is not None and new_data != prev_data:
            print("Nuevos datos encontrados. Transmitiendo...")
            await broadcast_new_data({"type": "callsUpdate", "payload": {"getCallsOnHoldData": new_data}})
            prev_data = new_data
            
        await asyncio.sleep(5)