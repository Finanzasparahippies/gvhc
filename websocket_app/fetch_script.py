# C:\Users\Agent\Documents\Zoom\config\files\gvhc\websocket_app\fetch_script.py

import asyncio
import requests
import json
# Use relative import (single dot for siblings in the same package)

DJANGO_PROXY_URL = "https://gvhc-backend.onrender.com/api/dashboards/proxy/generic/" 

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
