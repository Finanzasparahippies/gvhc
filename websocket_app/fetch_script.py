# websocket_app/fetch_script.py

import httpx
import json

from dashboards.utils import convert_query_times_to_utc, convert_result_datetimes_to_local
from django.conf import settings 


async def _forward_to_sharpen_async(endpoint: str, full_payload: dict):
    """Función base que realiza la llamada asíncrona a Sharpen."""
    from urllib.parse import urljoin # Add this import if not already there

    url = urljoin(settings.SHARPEN_API_BASE_URL, endpoint)
    print(f"DEBUG: Llamando a Sharpen URL: {url}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=full_payload, timeout=30.0)
            response.raise_for_status()
            
            # Procesamos la respuesta para convertir fechas, etc.
            result = response.json()
            processed_result = convert_result_datetimes_to_local(result)
            return processed_result
            
    except httpx.HTTPStatusError as e:
        print(f"Service Error: HTTP Status {e.response.status_code} from Sharpen: {e.response.text}")
        # Devuelve el error para que la vista pueda manejarlo
        return {"error": e.response.text, "status_code": e.response.status_code}
    except Exception as e:
        print(f"Service Error: Unexpected error forwarding to Sharpen: {e}")
        return {"error": str(e), "status_code": 500}


async def _call_sharpen_api_async(endpoint: str, payload: dict):
    """
    Función centralizada y asíncrona para llamar a cualquier endpoint de Sharpen.
    Esta función reemplaza la lógica de '_forward_to_sharpen' de tu vista.
    """
    auth_payload = {
        "cKey1": settings.SHARPEN_CKEY1,
        "cKey2": settings.SHARPEN_CKEY2,
        "uKey": settings.SHARPEN_UKEY,
    }
    
    if endpoint == "V2/query/":
        original_query = payload.get("q", "")
        converted_query = convert_query_times_to_utc(original_query)
        payload["q"] = converted_query
        full_payload = {**auth_payload, **payload}
        return await _forward_to_sharpen_async(endpoint, full_payload)
        
    elif endpoint == "V2/queues/getCdrDetails/":
        control_payload = {
            "getRecording": "false",
            "getNotes": "",
            "getTranscription": ""
        }
        full_payload = {**auth_payload, **control_payload, **payload}
        return await _forward_to_sharpen_async(endpoint, full_payload)

    # Endpoint para las llamadas en espera (usado por el WebSocket)
    elif endpoint == "V2/queues/getCallsOnHold/":
        full_payload = {**auth_payload, **payload}
        return await _forward_to_sharpen_async(endpoint, full_payload)

    # Puedes añadir aquí otros manejos especiales de endpoints...
    # ...
    elif endpoint == "V2/voice/callRecordings/createRecordingURL/":
        full_payload = {**auth_payload, **payload}
        # With urljoin, you can pass the endpoint as Sharpen expects it.
        # If Sharpen truly wants 'V2/voice/callRecordings/createRecordingURL/',
        # then pass it with the trailing slash here.
        return await _forward_to_sharpen_async("V2/voice/callRecordings/createRecordingURL/", full_payload)

    # Manejo genérico por defecto para todos los demás endpoints
    else:
        full_payload = {**auth_payload, **payload}
        return await _forward_to_sharpen_async(endpoint, full_payload)

# Esta función ahora contiene la lógica para hablar con la API externa
async def fetch_calls_on_hold_data():
    """
    Obtiene los datos de las llamadas en espera llamando DIRECTAMENTE
    a la función de servicio de Sharpen.
    """
    endpoint = "V2/queues/getCallsOnHold/"
    payload = {} # El payload para este endpoint específico es vacío

    # ✅ ¡Llamada directa! No más proxy.
    data = await _call_sharpen_api_async(endpoint, payload)

    if data and "error" not in data:
        return data
    return {"getCallsOnHoldData": []}