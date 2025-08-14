# websocket_app/fetch_script.py

import httpx
import json
from urllib.parse import urljoin # Asegúrate de que esto está importado

from dashboards.utils import convert_query_times_to_utc, convert_result_datetimes_to_local
from django.conf import settings 
import logging
import datetime # Necesario para calcular rangos de fecha/hora si la API lo pide
from django.utils import timezone # Para manejar zonas horarias y fechas actuales

logger = logging.getLogger(__name__)

SQL_CALL_COUNT_BY_QUEUE  = """
    SELECT 
        `queue`.`queueName` AS "Queue Name", 
        COUNT(`commType`) AS "Call Count"
    FROM 
        `fathomvoice`.`fathomQueues`.`queueCallManager` 
    GROUP BY 
        `Queue Name`
"""
def parse_sharpen_query_result(data: dict) -> list[dict]:
    parsed = []
    columns = [col['name'] for col in data.get('columns', [])]
    for row in data.get('rows', []):
        row_dict = {}
        for i, value in enumerate(row):
            if i < len(columns):
                row_dict[columns[i]] = value
        parsed.append(row_dict)
    return parsed


async def _forward_to_sharpen_async(endpoint: str, full_payload: dict):
    """Función base que realiza la llamada asíncrona a Sharpen."""

    url = urljoin(settings.SHARPEN_API_BASE_URL, endpoint)
    logger.debug(f"DEBUG: Llamando a Sharpen URL: {url} con payload: {json.dumps(full_payload)}") # Añadir payload al log
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=full_payload, timeout=30.0)
            response.raise_for_status()
            
            # Procesamos la respuesta para convertir fechas, etc.
            result = response.json()
            processed_result = convert_result_datetimes_to_local(result)
            logger.debug(f"DEBUG: Respuesta de Sharpen para {endpoint}: {json.dumps(processed_result)}") # Log de la respuesta
            return processed_result
            
    except httpx.HTTPStatusError as e:
        logger.error(f"Service Error: HTTP Status {e.response.status_code} from Sharpen: {e.response.text}")
        # Devuelve el error para que la vista pueda manejarlo
        return {"error": e.response.text, "status_code": e.response.status_code}
    except Exception as e:
        logger.error(f"Service Error: Unexpected error forwarding to Sharpen: {e}")
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

    # Manejo genérico por defecto para todos los demás endpoints
    else:
        full_payload = {**auth_payload, **payload}
        return await _forward_to_sharpen_async(endpoint, full_payload)
    
async def fetch_agent_performance_data():
    """
    Obtiene los datos de rendimiento de los agentes de Sharpen para gamificación.
    Esto puede requerir un endpoint específico o una consulta SQL avanzada.
    """
    endpoint = "V2/query/" # Asumiendo que usarás V2/query/ con SQL para esto
    today_utc = timezone.now().astimezone(timezone.utc).strftime('%Y-%m-%d')

    sql_query = SQL_CALL_COUNT_BY_QUEUE 
    
    payload = {
        "method": "query",
        "q": sql_query,
        "global": False # Si el contexto es global o no para Sharpen
    }

    try:
        data = await _call_sharpen_api_async(endpoint, payload)

        if data and "error" not in data and "rows" in data: # Asumiendo que los resultados de V2/query/ vienen en 'rows'
            # Sharpen's V2/query/ often returns data in a 'rows' list with 'columns'
            # You'll need to parse this into a list of dictionaries for easier use.
            parsed_data = parse_sharpen_query_result(data)
            
            for agent in parsed_data:
                if 'quality_score' in agent:
                    try:
                        agent['quality_score'] = float(agent['quality_score'] or 0)
                    except ValueError:
                        agent['quality_score'] = 0.0

                if 'issue_resolution_rate' in agent:
                    try:
                        agent['issue_resolution_rate'] = float(agent['issue_resolution_rate'] or 0)
                    except ValueError:
                        agent['issue_resolution_rate'] = 0.0

                if 'calls_handled_today' in agent:
                    try:
                        agent['calls_handled_today'] = int(agent['calls_handled_today'] or 0)
                    except ValueError:
                        agent['calls_handled_today'] = 0

            logger.info(f"Fetched {len(parsed_data)} agents performance data from Sharpen via SQL.")
            return parsed_data
        
        logger.warning(f"No se recibieron datos de rendimiento de agentes de Sharpen o hubo un error: {data.get('error', 'Desconocido')}. Retornando vacío.")
        return []
    except Exception as e:
        logger.error(f"Error al obtener datos de rendimiento de Sharpen: {e}", exc_info=True)
        return []

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
    logger.warning("No data or error received from Sharpen for getCallsOnHoldData. Returning empty.")
    return {"getCallsOnHoldData": []}

async def fetch_live_queue_status_data():
    """
    Obtiene los datos de Live Queue Status llamando a la API de Sharpen con la consulta SQL avanzada.
    """
    endpoint = "V2/query/"

    sql_query = SQL_CALL_COUNT_BY_QUEUE 

    payload = {
        "method": "query",
        "q": sql_query,
        "global": False 
    }
    # Asegúrate que el COUNT(`commType`) tenga un alias para que sea una columna con nombre en el JSON.
    # He añadido "AS \"Call Count\"" como ejemplo. Ajusta el nombre según lo que necesites en el frontend.

    data = await _call_sharpen_api_async(endpoint, payload)

    if data and "error" not in data and "rows" in data:
        # Parsear los resultados de V2/query/ de 'rows' y 'columns'
        parsed_data = parse_sharpen_query_result(data)
        return {"liveQueueStatus": parsed_data} # Envuelve en el dict esperado por tu consumer
    logger.warning("No data or error received from Sharpen for Live Queue Status. Returning empty.")
    return {"liveQueueStatus": []}
