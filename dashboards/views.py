import requests
import json
import os
from dotenv import load_dotenv
from pathlib import Path
import logging
import re
from django.http import StreamingHttpResponse, JsonResponse, HttpResponse
from rest_framework.views import APIView, View
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from bs4 import BeautifulSoup # Importar BeautifulSoup
from datetime import datetime # Importar datetime
import pytz
from urllib.parse import urlparse, parse_qs

BASE_DIR = Path(__file__).resolve().parent.parent
print(BASE_DIR / '.env')

load_dotenv(dotenv_path=BASE_DIR / '.env', override=True) 
# Create your views here.
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HERMOSILLO_TZ = pytz.timezone('America/Hermosillo') 
UTC_TZ = pytz.utc # Zona horaria UTC para localizar los datetimes

SHARPEN_API_BASE_URL = os.getenv('SHARPEN_API_BASE_URL')

def get_sharpen_audio_url(mixmon_file_name: str, recording_key: str) -> str | None:
    """
    Llama a la API de Sharpen para obtener una nueva URL de audio para una grabación.
    """
    endpoint = "V2/voice/callRecordings/createRecordingURL"
    cKey1 = os.getenv('SHARPEN_CKEY1')
    cKey2 = os.getenv('SHARPEN_CKEY2')
    uKey = os.getenv('SHARPEN_UKEY')

    if not all([cKey1, cKey2, uKey]):
        logger.error("Error: Las claves de Sharpen no están configuradas para la renovación de URLs.")
        return None

    payload = {
        "cKey1": cKey1, 
        "cKey2": cKey2, 
        "uKey": uKey,
        "uniqueID": recording_key, 
        "fileName": mixmon_file_name
    }
    
    api_url = f"{SHARPEN_API_BASE_URL}/{endpoint}/"
    logger.info(f"Solicitando nueva URL de audio a Sharpen: {api_url}")

    try:
        response = requests.post(api_url, json=payload, timeout=15)
        response.raise_for_status()
        result = response.json()
        
        if result.get('status') == 'successful' and result.get('url'):
            logger.info(f"Nueva URL de Sharpen obtenida exitosamente: {result['url']}")
            return result['url']
        else:
            logger.error(f"La respuesta de Sharpen para nueva URL no fue exitosa: {result}")
            return None
            
    except requests.RequestException as e:
        logger.error(f"Error al solicitar nueva URL de audio a Sharpen: {e}")
        return None
    except requests.exceptions.JSONDecodeError:
        logger.error(f"Respuesta no-JSON de Sharpen al solicitar nueva URL: {response.text}")
        return None


def convert_query_times_to_utc(query: str) -> str:
    """
    Busca fechas en formato 'YYYY-MM-DD HH:MM:SS' en una consulta SQL,
    asume que están en hora de Hermosillo, las convierte a UTC y las reemplaza.
    Utiliza dos patrones regex para mayor robustez.
    """
    datetime_pattern = re.compile(r"""
        (['"])                                          # Comilla de apertura (grupo 1)
        (\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}(?::\d{2})?)   # Fecha/hora con T o espacio (grupo 2)
        \1                                              # Comilla de cierre (referencia a grupo 1)
    """, re.IGNORECASE | re.VERBOSE)

    def convert_to_utc_string(local_time_str: str) -> str:
        """Función auxiliar para convertir un string de fecha local a UTC."""
        formats = [
            "%Y-%m-%dT%H:%M:%S", 
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%d %H:%M:%S", 
            "%Y-%m-%d %H:%M"
        ]        
        dt_local = None
        for fmt in formats:
            try:
                dt_local = datetime.strptime(local_time_str, fmt)
                break
            except ValueError:
                continue
        if dt_local is None:
            logger.warning(f"No se pudo parsear la fecha/hora para conversión a UTC: '{local_time_str}'. Se dejará sin modificar.")
            return local_time_str # Devuelve el string original

        dt_localized = HERMOSILLO_TZ.localize(dt_local)
        dt_utc = dt_localized.astimezone(UTC_TZ)
        utc_time_str = dt_utc.strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"Conversión de fecha: '{local_time_str}' (Hermosillo) -> '{utc_time_str}' (UTC)")
        return utc_time_str
    
    def replacer(match):
        quote_char = match.group(1) # Captura si es comilla simple o doble
        local_time_str = match.group(2)
        
        converted_time_str = convert_to_utc_string(local_time_str)
        # Reconstruye el string con el mismo tipo de comilla que se encontró
        return f"{quote_char}{converted_time_str}{quote_char}"

    # Aplica la conversión usando el nuevo patrón y la función replacer
    # Usamos sub para reemplazar todas las ocurrencias
    final_query = datetime_pattern.sub(replacer, query)
    
    return final_query

def convert_result_datetimes_to_local(result: dict) -> dict:
    """
    Convierte los campos de fecha/hora en la respuesta 'result' de UTC a hora local (Hermosillo).
    """
    potential_time_field_names  = [
                'startTime', 'StartTime', 'answerTime', 'AnswerTime', 'endTime', 'EndTime', 'created_at', 'updated_at', 'timestamp', 'intervals',
                'lastLogin', 'lastLogout', 'currentStatusDuration', 'lastCallTime', 'lastPauseTime', 'pauseTime', 'PauseTime', 'loginTime', 'LoginTime',
                'logoutTime', 'LogoutTime', 'lastStatusChange'
    ]
    data_to_process = None
    is_table_string = False
    is_single_object = False # Nueva bandera para saber si es un objeto único


    if 'data' in result and isinstance(result['data'], list):
        data_to_process = result['data']
        logger.debug("Procesando fechas en la clave 'data' (lista).")
    elif 'getAgentsData' in result and isinstance(result['getAgentsData'], list):
        data_to_process = result['getAgentsData']
        logger.debug("Procesando fechas en la clave 'getAgentsData' (lista de agentes).")

    elif 'table' in result and isinstance(result['table'], str):

        try:
            table_data = json.loads(result['table'])
            if isinstance(table_data, list):
                data_to_process = table_data
                is_table_string = True # Marcamos que viene de un string 'table'
                logger.debug("Procesando fechas en la clave 'table' (parsed JSON string).")
            else:
                data_to_process = [table_data]
                is_table_string = True
                is_single_object = True
                logger.debug("Procesando fechas en la clave 'table' (parsed JSON string, objeto único).")
        except json.JSONDecodeError as e:
            logger.error(f"Error al parsear el JSON de la clave 'table': {e}. El contenido era: {result.get('table')}")
    elif 'getAgentStatusData' in result and isinstance(result['getAgentStatusData'], dict):
            data_to_process = [result['getAgentStatusData']] # Envuelve el objeto en una lista para procesarlo
            is_single_object = True # Marca que es un objeto único
            logger.debug("Procesando fechas en la clave 'getAgentStatusData' (objeto único).")
    elif isinstance(result, dict): # Si el resultado completo es un dict y no tiene las claves anteriores
            # Esto podría ser para respuestas donde la data viene directamente en el root del JSON
            # (aunque menos común para APIs que devuelven data tabulada)
            # Aquí, podrías decidir si quieres procesar el diccionario completo
            # Por ahora, nos enfocamos en las claves conocidas.
            pass
    
    if data_to_process is None:
        logger.info("No se encontraron datos procesables ('data' o 'table' como lista) para la conversión de fechas. Devolviendo resultado original.")
        return result

    # Ahora procesa los datos
    processed_data = []
    for row in data_to_process:
        if not isinstance(row, dict):
            logger.warning(f"Se encontró una fila no-diccionario en los datos procesables: {row}. Saltando.")
            processed_data.append(row) # Incluye la fila original si no es un diccionario
            continue
        modified_row = row.copy() 

        for key, value in modified_row.items():
            # Normaliza la clave para la comparación para ser más flexible
            normalized_key_for_comparison = key.lower().replace(' ', '')
            
            # Comprueba si el nombre del campo está en nuestra lista de nombres de campos de tiempo
            # O si el nombre normalizado sugiere que es un campo de tiempo
            is_potential_time_field = key in potential_time_field_names or \
                any(name.lower().replace(' ', '') == normalized_key_for_comparison for name in potential_time_field_names)

            if is_potential_time_field and isinstance(value, str) and value:
                try:
                    # Intenta parsear con el formato común "YYYY-MM-DD HH:MM:SS"
                    dt_utc = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                    dt_utc_localized = UTC_TZ.localize(dt_utc)
                    dt_local = dt_utc_localized.astimezone(HERMOSILLO_TZ)
                    modified_row[key] = dt_local.strftime("%Y-%m-%d %H:%M:%S")
                    # logger.info(f"Conversión de fecha para campo '{key}': '{value}' (UTC) -> '{row[key]}' (Hermosillo)")
                except ValueError:
                    logger.warning(f"Formato de fecha inesperado para campo '{key}', valor '{value}'. Intentando otros formatos...")
                    # Podrías añadir más intentos de parseo aquí si esperas otros formatos
                    # Por ejemplo, si los segundos son opcionales o si hay milisegundos.
                    try: # Intento para el formato ISO si es que Sharpen lo usa en algún campo
                        dt_utc = datetime.fromisoformat(value.replace('Z', '+00:00')) # Manejar 'Z' para UTC
                        dt_utc_localized = UTC_TZ.localize(dt_utc) if dt_utc.tzinfo is None else dt_utc
                        dt_local = dt_utc_localized.astimezone(HERMOSILLO_TZ)
                        modified_row[key] = dt_local.strftime("%Y-%m-%d %H:%M:%S")
                        logger.debug(f"Conversión ISO para campo '{key}': '{value}' (UTC) -> '{row[key]}' (Hermosillo)")
                    except ValueError:
                        logger.warning(f"No se pudo parsear la fecha '{value}' con formatos conocidos para campo '{key}'. Dejando original.")
                except Exception as e:
                    logger.error(f"Error inesperado durante la conversión de fecha para campo '{key}', valor '{value}'. Error: {e}")
        processed_data.append(modified_row) # Agrega la fila procesada

    
    # Si los datos originales vinieron de un string 'table', vuelve a serializar
    if is_table_string:
        if is_single_object:
            result['table'] = json.dumps(processed_data[0])
            logger.info("Fechas convertidas a zona horaria local y re-serializadas en 'table'.")
        else: # Si vinieron de 'data'
            result['table'] = json.dumps(processed_data)
            logger.info("Fechas convertidas a zona horaria local en 'data'.")
            
    elif 'data' in result and isinstance(result['data'], list):
        result['data'] = processed_data
        logger.info("Fechas convertidas a zona horaria local en 'data'.")
    elif 'getAgentsData' in result and isinstance(result['getAgentsData'], list):
        result['getAgentsData'] = processed_data
        logger.info("Fechas convertidas a zona horaria local en 'getAgentsData'.")
    elif 'getAgentStatusData' in result and isinstance(result['getAgentStatusData'], dict):
        result['getAgentStatusData'] = processed_data[0] # Desenvuelve el objeto de la lista
        logger.info("Fechas convertidas a zona horaria local en 'getAgentStatusData'.")
    return result



def stream_audio_from_url(audio_url: str, recording_key: str):
    """Función auxiliar para hacer streaming de un audio desde una URL."""
    try:
        logger.info(f"Intentando descargar y hacer streaming del archivo de audio de: {audio_url}")
        audio_response = requests.get(audio_url, stream=True, timeout=60)
        audio_response.raise_for_status()

        content_type = audio_response.headers.get('Content-Type', 'audio/wav')
        
        # A veces S3 devuelve 'binary/octet-stream', nos aseguramos que sea un tipo de audio
        if 'audio/' not in content_type:
            logger.warning(f"Content-Type inesperado ('{content_type}'). Se forzará a 'audio/wav'.")
            content_type = 'audio/wav'

        response = StreamingHttpResponse(audio_response.iter_content(chunk_size=8192), content_type=content_type)
        response['Content-Disposition'] = f'inline; filename="{recording_key}.wav"'
        return response

    except requests.HTTPError as e:
        logger.error(f"Error HTTP al descargar audio para {recording_key}: {e.response.status_code}")
        return JsonResponse({"error": f"No se pudo descargar el audio: {e.response.text}"}, status=e.response.status_code)
    except requests.RequestException as e:
        logger.error(f"Error de red al descargar audio para {recording_key}: {e}")
        return JsonResponse({"error": "Error de comunicación con el servidor de audio."}, status=502)

class SharpenAudioProxyView(View): # Usamos View en lugar de APIView porque no manejamos JSON de entrada/salida directamente
    permission_classes = [AllowAny] # O ajusta tus permisos según sea necesario

    def get(self, request, *args, **kwargs):
        # Aquí obtenemos los parámetros necesarios de la URL.
        # Asumimos que el frontend enviará `mixmonFileName` y `uniqueID` como query parameters.
        mixmon_file_name = request.GET.get('mixmonFileName')
        unique_id = request.GET.get('uniqueID')

        if not mixmon_file_name or not unique_id:
            logger.error("Faltan los parámetros 'mixmonFileName' o 'uniqueID' para la solicitud de audio.")
            return JsonResponse({"error": "Parámetros de audio incompletos."}, status=400)

        logger.info(f"Solicitud de audio proxy recibida para mixmonFileName: {mixmon_file_name}, uniqueID: {unique_id}")

        # 1. Obtener la URL presignada de Sharpen
        sharpen_audio_url = get_sharpen_audio_url(mixmon_file_name, unique_id)

        if not sharpen_audio_url:
            logger.error(f"No se pudo obtener la URL de audio de Sharpen para {mixmon_file_name}.")
            return JsonResponse({"error": "No se pudo obtener la URL de audio de Sharpen."}, status=500)

        logger.info(f"URL de audio de Sharpen obtenida: {sharpen_audio_url}")

        # 2. Stream el audio desde la URL de Sharpen y añadir cabeceras CORS
        # La función `stream_audio_from_url` ya devuelve un StreamingHttpResponse.
        # Necesitamos agregar las cabeceras CORS a esa respuesta.
        response = stream_audio_from_url(sharpen_audio_url, unique_id)
        origin = request.META.get('HTTP_ORIGIN')
        if origin:
            # Aquí podrías validar si el origen está permitido en tu lista blanca
            # Para fines de depuración, permitimos cualquier origen si se envía
            response['Access-Control-Allow-Origin'] = origin
        else:
        # Añadir las cabeceras CORS a la respuesta del streaming.
        # Asegúrate de que tu frontend (ej. http://localhost:3000, o tu dominio de producción)
        # esté en la lista de orígenes permitidos.
            response['Access-Control-Allow-Origin'] = '*'
        # Para producción, es mejor especificar:
        # response['Access-Control-Allow-Origin'] = 'https://tu-dominio-produccion.com'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization' # Si tu frontend envía alguna cabecera
        response['Access-Control-Allow-Credentials'] = 'true' # Si manejas cookies o credenciales

        return response

    def options(self, request, *args, **kwargs):
        # Manejar las solicitudes OPTIONS (preflight) para CORS
        response = HttpResponse(status=204) # 204 No Content para preflight
        origin = request.META.get('HTTP_ORIGIN')
        if origin:
            response['Access-Control-Allow-Origin'] = origin
        else:
            response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Access-Control-Max-Age'] = '86400' # Cache preflight por 24 horas
        logger.info(f"SharpenAudioProxyView: Recibida solicitud OPTIONS (preflight) desde {origin}.")
        return response

class SharpenApiGenericProxyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):

        cKey1 = os.getenv('SHARPEN_CKEY1')
        cKey2 = os.getenv('SHARPEN_CKEY2')
        uKey = os.getenv('SHARPEN_UKEY') # Ensure uKey is also available for the backend

        if not all([cKey1, cKey2, uKey]):
            logger.error("Error: Las claves de Sharpen no están configuradas para la renovación de URLs.")
            return None
        
        try:
            # DRF ya parsea el JSON, no necesitas json.loads(request.body)
            data = request.data
        except Exception:
            logger.error("Invalid JSON in request body.")
            return JsonResponse({"status": "error", "description": "Invalid JSON"}, status=400)

        endpoint = data.get('endpoint')
        payload = data.get('payload')

        logger.info(f"BACKEND Proxy: endpoint recibido='{endpoint}', payload recibido={payload}")
        
        if not endpoint or not isinstance(payload, dict):
            logger.error("Faltan campos obligatorios 'endpoint' o 'payload'.")
            return JsonResponse({"status": "error", "description": "Missing 'endpoint' or invalid 'payload'"}, status=400)
        
        auth_payload = {
            "cKey1": cKey1,
            "cKey2": cKey2,
            "uKey": uKey,
        }

        # Manejo de endpoints específicos
        if endpoint == "V2/voice/callRecordings/createRecordingURL":
            mixmon_file_name = payload.get('fileName')
            recording_key = payload.get('uniqueID') or payload.get('queueCallManagerID')
            if not mixmon_file_name and not recording_key: 
                    logger.error("createRecordingURL: Faltan uniqueID o fileName en el payload.")
                    return JsonResponse({"status": "error", "description": "Missing uniqueID or fileName for audio URL request"}, status=400)

                # Usa `recording_key` como `uniqueID` y `mixmon_file_name` como `fileName`
            sharpen_url = get_sharpen_audio_url(mixmon_file_name, recording_key)
            if sharpen_url:
                logger.info(f"createRecordingURL: URL obtenida para el frontend: {sharpen_url}")
                return JsonResponse({"status": "successful", "url": sharpen_url})
            else:
                logger.error("createRecordingURL: Fallo al obtener la URL de Sharpen.")
                return JsonResponse({"status": "error", "description": "Failed to get Sharpen recording URL"}, status=500)
        
        if endpoint == "V2/query/":
            # Aquí sí necesitamos el full_payload para enviar a Sharpen después de modificar la query.
            # Convertimos la query antes de añadir las claves de auth y reenviar.
            original_query = payload.get("q", "")
            converted_query = convert_query_times_to_utc(original_query)
            payload["q"] = converted_query
            
            logger.info(f"SQL original: {original_query}")
            logger.info(f"SQL convertida a UTC: {converted_query}")
            
            # Ahora creamos el full_payload para reenviar con las claves de auth
            auth_payload = self._get_auth_payload()
            full_payload_for_forward = {**auth_payload, **payload}
            return self._forward_to_sharpen(endpoint, full_payload_for_forward)
        
        elif endpoint == "V2/queues/getCdrDetails/": # Use elif
            logger.info("Manejando endpoint 'getCdrDetails'. Se añadirán claves de auth y parámetros de control.")
            control_payload = {
                "getRecording": "false",
                "getNotes": "",
                "getTranscription": ""
            }
            
            # 1. Obtenemos las claves de autenticación
            full_payload = {**auth_payload, **control_payload, **payload}
            return self._forward_to_sharpen(endpoint, full_payload) 
        
        else:
            logger.info(f"Manejando endpoint genérico: '{endpoint}'.")
            full_payload = {**auth_payload, **payload} # Just combine base auth with client's payload
            return self._forward_to_sharpen(endpoint, full_payload)

    def _get_auth_payload(self):
        """
        Retorna un diccionario con las claves de autenticación de Sharpen.
        """
        return {
            "cKey1": os.getenv('SHARPEN_CKEY1'),
            "cKey2": os.getenv('SHARPEN_CKEY2'),
            "uKey": os.getenv('SHARPEN_UKEY'),
            # Estos campos parecen ser parte del payload general que Sharpen espera
            # pero si no se usan, pueden causar problemas. Es mejor solo agregarlos
            # si son estrictamente necesarios para *todas* las llamadas API genéricas.
            # Si no son siempre necesarios, se pueden omitir de aquí
            # y añadirlos específicamente donde se requieran.
            # Por ahora, los dejaré, pero considera si son realmente necesarios globalmente.
            "recordID": "",
            "pKey2": "",
            "fileName": "",
            "make": "",
            "callTag": "",
            "clickToCallID": "",
            "callRecordID": "",
        }

    def _forward_to_sharpen(self, endpoint, payload):
        """
        Reenvía la petición con el payload completo (incluyendo claves de auth) a Sharpen.
        """
        url = f"{SHARPEN_API_BASE_URL}{endpoint}"
        logger.info(f"Enviando petición a Sharpen URL: {url}")
        logger.debug(f"Payload final enviado a Sharpen: {payload}") # Útil para depurar

        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()

            try:
                result = response.json()
                # Aplica la conversión de fechas a la respuesta si es un JSON
                processed_result = convert_result_datetimes_to_local(result)
                logger.info("Respuesta JSON procesada correctamente y convertida a zona horaria local.")
                return JsonResponse(processed_result)
            except requests.exceptions.JSONDecodeError:
                logger.warning(f"Respuesta de Sharpen desde '{endpoint}' no es JSON válida. Devolviendo como texto plano.")
                # Si la respuesta no es JSON, la devolvemos tal cual con su Content-Type original
                return HttpResponse(response.text, status=response.status_code, content_type=response.headers.get('Content-Type', 'text/plain'))

        except requests.exceptions.HTTPError as e:
            logger.error(f"Error HTTP {e.response.status_code} desde Sharpen para {endpoint}: {e.response.text}")
            return JsonResponse({"status": "error", "description": e.response.text}, status=e.response.status_code)
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión con Sharpen para {endpoint}: {e}")
            return JsonResponse({"status": "error", "description": "No se pudo conectar a Sharpen"}, status=503)
        except Exception as e:
            logger.exception(f"Error inesperado en _forward_to_sharpen para {endpoint}")
            return JsonResponse({"status": "error", "description": "Error interno en el servidor"}, status=500)
