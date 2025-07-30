# websocket_app/fetch_script.py

import httpx
import json
from urllib.parse import urljoin # Asegúrate de que esto está importado

from dashboards.utils import convert_query_times_to_utc, convert_result_datetimes_to_local
from django.conf import settings 
import logging

logger = logging.getLogger(__name__)

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
    
async def fetch_agent_performance_data():
    """
    Obtiene los datos de rendimiento de los agentes de Sharpen para gamificación.
    Esto puede requerir un endpoint específico o una consulta SQL avanzada.
    """
    endpoint = "V2/query/" # Asumiendo que usarás V2/query/ con SQL para esto

    # Define la consulta SQL para obtener las métricas de rendimiento de los agentes.
    # Necesitas saber qué tablas y campos de Sharpen contienen estos datos.
    # Este es un EJEMPLO. Deberás ajustarlo a tu estructura de datos real de Sharpen.
    # Asumo que 'fathomvoice.fathomQueues.queueCallManager' tiene información por agente.
    # O tal vez hay una tabla de agentes o métricas de usuario.
    
    # MUY IMPORTANTE: La consulta SQL debe retornar los campos que necesitas
    # para tu lógica de puntos (ej. 'Username', 'CallsHandled', 'QualityScore').
    # Asegúrate de que los alias (AS "...") coincidan con las claves que esperas en Python.
    
    # La consulta que tienes en el comentario de tu código:
    # "username": "juan.perez", "calls_handled_today": 5, "quality_score": 90
    # Esto implica que necesitas obtener esos datos de Sharpen.
    
    # EJEMPLO DE CONSULTA (ADAPTA ESTO A LO QUE SHARPEN PUEDA DARTE):
    # Si Sharpen tiene un endpoint o una vista para métricas de agentes individuales:
    # payload = {} # O algún payload si el endpoint es directo
    # data = await _call_sharpen_api_async("V2/agents/getPerformanceMetrics/", payload)
    
    # Si usas V2/query/ con SQL:
    payload = {
        "method": "query",
        "q": """
            SELECT
                `agent_metrics`.`agentUsername` AS "username",
                COUNT(`calls`.`callId`) AS "calls_handled_today",
                AVG(`calls`.`qualityScore`) AS "quality_score",
                AVG(`calls`.`issueResolutionRate`) AS "issue_resolution_rate"
            FROM
                `fathomvoice`.`fathomQueues`.`agent_metrics` AS agent_metrics
            LEFT JOIN
                `fathomvoice`.`fathomQueues`.`calls` AS calls ON agent_metrics.agentId = calls.agentId
            WHERE
                DATE(`calls`.`callDate`) = CURDATE() -- O algún filtro de tiempo
            GROUP BY
                "username"
        """,
        "global": "false"
    }

    try:
        data = await _call_sharpen_api_async(endpoint, payload)

        if data and "error" not in data and "rows" in data: # Asumiendo que los resultados de V2/query/ vienen en 'rows'
            # Sharpen's V2/query/ often returns data in a 'rows' list with 'columns'
            # You'll need to parse this into a list of dictionaries for easier use.
            parsed_data = []
            columns = [col['name'] for col in data.get('columns', [])]
            for row in data['rows']:
                agent_dict = {}
                for i, value in enumerate(row):
                    if i < len(columns):
                        agent_dict[columns[i]] = value
                parsed_data.append(agent_dict)
            
            logger.debug(f"Datos de rendimiento de agentes de Sharpen: {parsed_data}")
            return parsed_data
        
        logger.warning("No se recibieron datos o hubo un error de Sharpen para el rendimiento de agentes. Retornando vacío.")
        return []
    except Exception as e:
        logger.error(f"Error al obtener datos de rendimiento de Sharpen: {e}")
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
    # La consulta SQL avanzada que proporcionaste, escapada correctamente.
    # Nota: Asegúrate de que Sharpen espera 'advanced' como un string JSON escapado.
    # Si 'q' es suficiente, usa 'q'. Si no, ajusta el payload a lo que Sharpen realmente necesita.
    # Aquí asumo que 'q' es el campo esperado para la SQL.
    # Si "advanced" es el campo, el payload debería ser {"advanced": "...", "global": "false"}
    # La API que pasaste es: `{"advanced":"\"SELECT ... LIMIT 1\"","global":"false"}`
    # Esto significa que el valor de "advanced" ya es una cadena JSON escapada.
    # Si _call_sharpen_api_async maneja "advanced" y "global" directamente:
    payload = {
        "method": "query", # Necesario si V2/query/ espera esto
        "q": """SELECT `queue`.`queueName` AS "Queue Name", COUNT(`commType`) AS "Call Count", FROM_UNIXTIME(FLOOR(UNIX_TIMESTAMP(NOW())/(5))*(5)) AS "intervals" FROM `fathomvoice`.`fathomQueues`.`queueCallManager` GROUP BY `Queue Name` UNION (SELECT null, null, FROM_UNIXTIME(FLOOR(UNIX_TIMESTAMP(NOW())/(5))*(5)) AS "intervals") LIMIT 1""",
        "global": "false" # Esto es parte del payload de la API, no de la SQL
    }
    # Asegúrate que el COUNT(`commType`) tenga un alias para que sea una columna con nombre en el JSON.
    # He añadido "AS \"Call Count\"" como ejemplo. Ajusta el nombre según lo que necesites en el frontend.

    data = await _call_sharpen_api_async(endpoint, payload)

    if data and "error" not in data:
        # Aquí puedes querer transformar los datos si el formato de Sharpen no es exactamente el que quieres enviar al frontend.
        return data
    return {"liveQueueStatus": []} # Devuelve un array vacío si no hay datos o hay error
