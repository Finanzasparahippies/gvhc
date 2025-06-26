import requests
import json
import os
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

# Create your views here.
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HERMOSILLO_TZ = pytz.timezone('America/Hermosillo') 
UTC_TZ = pytz.utc # Zona horaria UTC para localizar los datetimes

SHARPEN_API_BASE_URL = "https://api-current.iz1.sharpen.cx/"
SHARPEN_AWS_S3_API_BASE_URL = "https://api.fathomvoice.com/" 

def get_sharpen_audio_url(recording_key: str) -> str | None:
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

def get_sharpen_aws_s3_url(file_name: str) -> str | None:
    """
    Llama a la API de Sharpen para obtener una URL pre-firmada directamente desde AWS S3.
    Utiliza el endpoint V2/aws/getObjectLink/ como se describe en la nueva documentación.
    """
    endpoint = "V2/aws/getObjectLink/"
    cKey1 = os.getenv('SHARPEN_CKEY1')
    cKey2 = os.getenv('SHARPEN_CKEY2')

    if not all([cKey1, cKey2]):
        logger.error("Error: Las claves de Sharpen (cKey1, cKey2) no están configuradas para obtener URL de S3.")
        return None

    # El tipo de contenido "Multipart Form" generalmente se traduce a form-urlencoded
    # en requests si los datos se pasan en el parámetro `data`.
    payload = {
        "cKey1": cKey1,
        "cKey2": cKey2,
        "bucketName": "mixrec",
        "fileName": file_name,
    }

    api_url = f"{SHARPEN_AWS_S3_API_BASE_URL}{endpoint}" # Notar que no hay '/' al final de endpoint
    logger.info(f"PRIORITARIO: Solicitando URL de S3 a Sharpen (endpoint getObjectLink): {api_url}")
    logger.debug(f"Payload enviado para get_sharpen_aws_s3_url: {payload}")

    try:
        # Usamos `data` en lugar de `json` para enviar como form-urlencoded, que es lo que
        # "Multipart Form" a menudo implica para este tipo de peticiones simples.
        response = requests.post(api_url, data=payload, timeout=15)
        response.raise_for_status()
        result = response.json()

        # La documentación menciona quitar backslashes. Aunque `json.loads` normalmente
        # maneja esto, si la URL llega con backslashes literales (lo cual es inusual para URL),
        # esta limpieza asegura que sea una URL válida.
        s3_url = result.get('url')
        if s3_url:
            cleaned_url = s3_url.replace('\\', '')
            logger.info(f"PRIORITARIO: URL de S3 de Sharpen obtenida exitosamente: {cleaned_url}")
            return cleaned_url
        else:
            logger.error(f"PRIORITARIO: La respuesta de Sharpen para URL de S3 no fue exitosa o no contiene 'url': {result}")
            return None

    except requests.RequestException as e:
        logger.error(f"PRIORITARIO: Error al solicitar URL de S3 a Sharpen: {e}")
        return None
    except requests.exceptions.JSONDecodeError:
        logger.error(f"PRIORITARIO: Respuesta no-JSON de Sharpen al solicitar URL de S3: {response.text}")
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

class ProxyRecordingView(View):
    def get(self, request, recording_key):        
        # Usamos la función de servicio centralizada
        actual_audio_url = get_sharpen_audio_url(recording_key)
        logger.warning(f"actual aduio url: {recording_key}.")

        if not actual_audio_url:
            # Si falla, podemos intentar el método de scraping como fallback
            logger.warning(f"No se pudo obtener la URL vía API. Intentando scraping de HTML para {recording_key}.")
            sharpen_html_page_url = f"https://api-current.iz1.sharpen.cx/V2/voice/callRec/{recording_key}"
            try:
                html_response = requests.get(sharpen_html_page_url, timeout=30)
                html_response.raise_for_status()
                soup = BeautifulSoup(html_response.text, 'html.parser')
                audio_tag = soup.find('source') or soup.find('audio')
                if audio_tag and audio_tag.get('src'):
                    actual_audio_url = audio_tag['src']
                    logger.info(f"URL de audio encontrada vía scraping: {actual_audio_url}")
                else:
                    logger.error("Fallback de scraping falló. No se encontró URL de audio.")
                    return JsonResponse({"error": "No se pudo obtener la URL de la grabación."}, status=504)
            except requests.RequestException as e:
                logger.error(f"Error durante el fallback de scraping: {e}")
                return JsonResponse({"error": "No se pudo obtener la URL de la grabación."}, status=504)

        if actual_audio_url:
            return stream_audio_from_url(actual_audio_url, recording_key)
        else:
            return JsonResponse({"error": "No se pudo resolver la URL del audio final."}, status=500)


class ProxyOldRecordingByMixmonView(View):
    """
    Vista para proxear grabaciones antiguas usando el mixmonFileName como uniqueID.
    """
    def get(self, request, mixmon_file_name):
        logger.info(f"Solicitud para proxear audio antiguo con mixmonFileName: {mixmon_file_name}")
        
        # Reutilizamos la lógica centralizada
        actual_audio_url = get_sharpen_aws_s3_url(mixmon_file_name) # rowIndex puede ser opcional

        if not actual_audio_url:
            logger.error(f"No se pudo obtener la URL de audio de Sharpen para mixmonFileName: {mixmon_file_name}")
            return JsonResponse({"error": "No se pudo obtener la URL del audio antiguo."}, status=500)
            
        return stream_audio_from_url(actual_audio_url, mixmon_file_name)


# def get_sharpen_audio_url(recording_key: str, row_index: str = None) -> str | None:
#     """
#     Llama a la API de Sharpen para obtener una nueva URL de audio para una grabación.
#     """
#     endpoint = "V2/voice/callRecordings/createRecordingURL"
#     cKey1 = os.getenv('SHARPEN_CKEY1')
#     cKey2 = os.getenv('SHARPEN_CKEY2')
#     uKey = os.getenv('SHARPEN_UKEY')

#     if not all([cKey1, cKey2, uKey]):
#         logger.error("Error: Las claves de Sharpen no están configuradas para la renovación de URLs.")
#         return None

#     payload = {
#         "cKey1": cKey1,
#         "cKey2": cKey2,
#         "uKey": uKey,
#         "uniqueID": recording_key,
#         "rowIndex": row_index
#     }
    
#     api_url = f"{SHARPEN_API_BASE_URL}{endpoint}/"
#     logger.info(f"Solicitando nueva URL de audio a Sharpen: {api_url}")
#     logger.debug(f"Payload enviado para get_sharpen_audio_url: {payload}")

#     try:
#         response = requests.post(api_url, json=payload, timeout=15)
#         response.raise_for_status()
#         result = response.json()
        
#         if result.get('status') == 'successful' and result.get('url'):
#             logger.info(f"Nueva URL de Sharpen obtenida exitosamente: {result['url']}")
#             return result['url']
#         else:
#             logger.error(f"La respuesta de Sharpen para nueva URL no fue exitosa: {result}")
#             return None
            
#     except requests.RequestException as e:
#         logger.error(f"Error al solicitar nueva URL de audio a Sharpen: {e}")
#         return None
#     except requests.exceptions.JSONDecodeError:
#         logger.error(f"Respuesta no-JSON de Sharpen al solicitar nueva URL: {response.text}")
#         return None
    
# def convert_query_times_to_utc(query: str) -> str:
#     """
#     Busca fechas en formato 'YYYY-MM-DD HH:MM:SS' en una consulta SQL,
#     asume que están en hora de Hermosillo, las convierte a UTC y las reemplaza.
#     Utiliza dos patrones regex para mayor robustez.
#     """
#     datetime_pattern = re.compile(r"""
#         (['"])                                  # Comilla de apertura (grupo 1)
#         (\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}(?::\d{2})?)   # Fecha/hora con T o espacio (grupo 2)
#         \1                                      # Comilla de cierre (referencia a grupo 1)
#     """, re.IGNORECASE | re.VERBOSE)

#     def convert_to_utc_string(local_time_str: str) -> str:
#         """Función auxiliar para convertir un string de fecha local a UTC."""
#         formats = [
#             "%Y-%m-%dT%H:%M:%S",
#             "%Y-%m-%dT%H:%M",
#             "%Y-%m-%d %H:%M:%S",
#             "%Y-%m-%d %H:%M"
#         ]        
#         dt_local = None
#         for fmt in formats:
#             try:
#                 dt_local = datetime.strptime(local_time_str, fmt)
#                 break
#             except ValueError:
#                 continue
#         if dt_local is None:
#             logger.warning(f"No se pudo parsear la fecha/hora para conversión a UTC: '{local_time_str}'. Se dejará sin modificar.")
#             return local_time_str # Devuelve el string original

#         dt_localized = HERMOSILLO_TZ.localize(dt_local)
#         dt_utc = dt_localized.astimezone(UTC_TZ)
#         utc_time_str = dt_utc.strftime("%Y-%m-%d %H:%M:%S")
#         logger.info(f"Conversión de fecha: '{local_time_str}' (Hermosillo) -> '{utc_time_str}' (UTC)")
#         return utc_time_str
    
#     def replacer(match):
#         quote_char = match.group(1) # Captura si es comilla simple o doble
#         local_time_str = match.group(2)
        
#         converted_time_str = convert_to_utc_string(local_time_str)
#         # Reconstruye el string con el mismo tipo de comilla que se encontró
#         return f"{quote_char}{converted_time_str}{quote_char}"

#     # Aplica la conversión usando el nuevo patrón y la función replacer
#     # Usamos sub para reemplazar todas las ocurrencias
#     final_query = datetime_pattern.sub(replacer, query)
    
#     return final_query

# def convert_result_datetimes_to_local(result: dict) -> dict:
#     """
#     Convierte los campos de fecha/hora en la respuesta 'result' de UTC a hora local (Hermosillo).
#     """
#     potential_time_field_names = [
#         'startTime', 'StartTime', 'answerTime', 'AnswerTime', 'endTime', 'EndTime', 'created_at', 'updated_at', 'timestamp', 'intervals',
#         'lastLogin', 'lastLogout', 'currentStatusDuration', 'lastCallTime', 'lastPauseTime', 'pauseTime', 'PauseTime', 'loginTime', 'LoginTime',
#         'logoutTime', 'LogoutTime', 'lastStatusChange'
#     ]
#     data_to_process = None
#     is_table_string = False
#     is_single_object = False

#     if 'data' in result and isinstance(result['data'], list):
#         data_to_process = result['data']
#         logger.debug("Procesando fechas en la clave 'data' (lista).")
#     elif 'getAgentsData' in result and isinstance(result['getAgentsData'], list):
#         data_to_process = result['getAgentsData']
#         logger.debug("Procesando fechas en la clave 'getAgentsData' (lista de agentes).")
#     elif 'table' in result and isinstance(result['table'], str):
#         try:
#             table_data = json.loads(result['table'])
#             if isinstance(table_data, list):
#                 data_to_process = table_data
#                 is_table_string = True
#                 logger.debug("Procesando fechas en la clave 'table' (parsed JSON string).")
#             else:
#                 data_to_process = [table_data]
#                 is_table_string = True
#                 is_single_object = True
#                 logger.debug("Procesando fechas en la clave 'table' (parsed JSON string, objeto único).")
#         except json.JSONDecodeError as e:
#             logger.error(f"Error al parsear el JSON de la clave 'table': {e}. El contenido era: {result.get('table')}")
#     elif 'getAgentStatusData' in result and isinstance(result['getAgentStatusData'], dict):
#         data_to_process = [result['getAgentStatusData']]
#         is_single_object = True
#         logger.debug("Procesando fechas en la clave 'getAgentStatusData' (objeto único).")
    
#     if data_to_process is None:
#         logger.info("No se encontraron datos procesables ('data' o 'table' como lista) para la conversión de fechas. Devolviendo resultado original.")
#         return result

#     processed_data = []
#     for row in data_to_process:
#         if not isinstance(row, dict):
#             logger.warning(f"Se encontró una fila no-diccionario en los datos procesables: {row}. Saltando.")
#             processed_data.append(row)
#             continue
#         modified_row = row.copy()

#         for key, value in modified_row.items():
#             normalized_key_for_comparison = key.lower().replace(' ', '')
            
#             is_potential_time_field = key in potential_time_field_names or \
#                 any(name.lower().replace(' ', '') == normalized_key_for_comparison for name in potential_time_field_names)

#             if is_potential_time_field and isinstance(value, str) and value:
#                 try:
#                     dt_utc = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
#                     dt_utc_localized = UTC_TZ.localize(dt_utc)
#                     dt_local = dt_utc_localized.astimezone(HERMOSILLO_TZ)
#                     modified_row[key] = dt_local.strftime("%Y-%m-%d %H:%M:%S")
#                 except ValueError:
#                     logger.warning(f"Formato de fecha inesperado para campo '{key}', valor '{value}'. Intentando otros formatos...")
#                     try:
#                         dt_utc = datetime.fromisoformat(value.replace('Z', '+00:00'))
#                         dt_utc_localized = UTC_TZ.localize(dt_utc) if dt_utc.tzinfo is None else dt_utc
#                         dt_local = dt_utc_localized.astimezone(HERMOSILLO_TZ)
#                         modified_row[key] = dt_local.strftime("%Y-%m-%d %H:%M:%S")
#                         logger.debug(f"Conversión ISO para campo '{key}': '{value}' (UTC) -> '{modified_row[key]}' (Hermosillo)")
#                     except ValueError:
#                         logger.warning(f"No se pudo parsear la fecha '{value}' con formatos conocidos para campo '{key}'. Dejando original.")
#                 except Exception as e:
#                     logger.error(f"Error inesperado durante la conversión de fecha para campo '{key}', valor '{value}'. Error: {e}")
#         processed_data.append(modified_row)

#     if is_table_string:
#         if is_single_object:
#             result['table'] = json.dumps(processed_data[0])
#             logger.info("Fechas convertidas a zona horaria local y re-serializadas en 'table' (objeto único).")
#         else:
#             result['table'] = json.dumps(processed_data)
#             logger.info("Fechas convertidas a zona horaria local y re-serializadas en 'table' (lista).")
            
#     elif 'data' in result and isinstance(result['data'], list):
#         result['data'] = processed_data
#         logger.info("Fechas convertidas a zona horaria local en 'data'.")
#     elif 'getAgentsData' in result and isinstance(result['getAgentsData'], list):
#         result['getAgentsData'] = processed_data
#         logger.info("Fechas convertidas a zona horaria local en 'getAgentsData'.")
#     elif 'getAgentStatusData' in result and isinstance(result['getAgentStatusData'], dict):
#         result['getAgentStatusData'] = processed_data[0]
#         logger.info("Fechas convertidas a zona horaria local en 'getAgentStatusData'.")
#     return result


# def stream_audio_from_url(audio_url: str, recording_key: str):
#     """Función auxiliar para hacer streaming de un audio desde una URL."""
#     try:
#         logger.info(f"Intentando descargar y hacer streaming del archivo de audio de: {audio_url}")
#         audio_response = requests.get(audio_url, stream=True, timeout=60)
#         audio_response.raise_for_status()

#         content_type = audio_response.headers.get('Content-Type', 'audio/wav')
        
#         if 'audio/' not in content_type:
#             logger.warning(f"Content-Type inesperado ('{content_type}'). Se forzará a 'audio/wav'.")
#             content_type = 'audio/wav'

#         response = StreamingHttpResponse(audio_response.iter_content(chunk_size=8192), content_type=content_type)
#         response['Content-Disposition'] = f'inline; filename="{recording_key}.wav"'
#         return response

#     except requests.HTTPError as e:
#         logger.error(f"Error HTTP al descargar audio para {recording_key}: {e.response.status_code}")
#         return JsonResponse({"error": f"No se pudo descargar el audio: {e.response.text}"}, status=e.response.status_code)
#     except requests.RequestException as e:
#         logger.error(f"Error de red al descargar audio para {recording_key}: {e}")
#         return JsonResponse({"error": "Error de comunicación con el servidor de audio."}, status=502)

# class ProxyRecordingView(View):
#     def get(self, request, recording_key):
#         row_index = request.GET.get('rowIndex')
        
#         actual_audio_url = get_sharpen_audio_url(recording_key, row_index)
        
#         if not actual_audio_url:
#             logger.warning(f"No se pudo obtener la URL vía API. Intentando scraping de HTML para {recording_key}.")
#             sharpen_html_page_url = f"https://api-current.iz1.sharpen.cx/V2/voice/callRec/{recording_key}"
#             try:
#                 html_response = requests.get(sharpen_html_page_url, timeout=30)
#                 html_response.raise_for_status()
#                 soup = BeautifulSoup(html_response.text, 'html.parser')
#                 audio_tag = soup.find('source') or soup.find('audio')
#                 if audio_tag and audio_tag.get('src'):
#                     actual_audio_url = audio_tag['src']
#                     logger.info(f"URL de audio encontrada vía scraping: {actual_audio_url}")
#                 else:
#                     logger.error("Fallback de scraping falló. No se encontró URL de audio.")
#                     return JsonResponse({"error": "No se pudo obtener la URL de la grabación."}, status=504)
#             except requests.RequestException as e:
#                 logger.error(f"Error durante el fallback de scraping: {e}")
#                 return JsonResponse({"error": "No se pudo obtener la URL de la grabación."}, status=504)

#         if actual_audio_url:
#             return stream_audio_from_url(actual_audio_url, recording_key)
#         else:
#             return JsonResponse({"error": "No se pudo resolver la URL del audio final."}, status=500)


# class ProxyOldRecordingByMixmonView(View):
#     """
#     Vista para proxear grabaciones antiguas usando el mixmonFileName como uniqueID.
#     """
#     def get(self, request, mixmon_file_name):
#         logger.info(f"Solicitud para proxear audio antiguo con mixmonFileName: {mixmon_file_name}")
        
#         actual_audio_url = get_sharpen_aws_s3_url(mixmon_file_name)

#         if not actual_audio_url:
#             logger.error(f"No se pudo obtener la URL de audio de Sharpen para mixmonFileName: {mixmon_file_name}")
#             actual_audio_url = get_sharpen_audio_url(mixmon_file_name) # rowIndex puede ser opcional
#             return JsonResponse({"error": "No se pudo obtener la URL del audio antiguo."}, status=500)
            
#         return stream_audio_from_url(actual_audio_url, mixmon_file_name)



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
            # Este manejador no necesita el full_payload con las claves de auth,
            # ya que llama directamente a `get_sharpen_audio_url` que las maneja.
            return self._handle_create_recording_url(payload)
        
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
            return self._forward_to_sharpen(endpoint, full_payload) # <--- ADDED RETURN HERE
        
        elif endpoint == "V2/queues/getInteraction/":
            logger.info("Manejando endpoint 'getInteraction'. Se añadirán claves de auth.")
            # The frontend payload for getInteraction already contains `queueCallManagerID` and `uKey`.
            # We combine it with the backend's core auth keys (cKey1, cKey2)
            # and override uKey from env if the frontend provides one.
            final_payload = {**auth_payload, **payload}
            if 'uKey' in payload and payload['uKey']: # Prioritize frontend's uKey if provided
                final_payload['uKey'] = payload['uKey']
            return self._forward_to_sharpen(endpoint, final_payload)
        
        elif endpoint == "V2/aws/getObjectLink/":
            logger.info("Manejando endpoint 'getAwsObjectLink'. Se añadirán claves de auth.")
            # The frontend payload for getObjectLink already contains `bucketName` and `fileName`.
            # We combine it with the backend's core auth keys.
            final_payload = {**auth_payload, **payload}
            return self._forward_to_sharpen(endpoint, final_payload)
        
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

    def _handle_create_recording_url(self, payload):
        """
        Maneja la solicitud para obtener una URL de grabación de Sharpen.
        Delega la lógica a la función `get_sharpen_audio_url`.
        """
        mixmon_file_name = payload.get('mixmonFileName')

        if mixmon_file_name:
            logger.info(f"Intentando obtener URL de S3 con mixmonFileName: {mixmon_file_name}")
            s3_url = get_sharpen_aws_s3_url(mixmon_file_name)
            if s3_url:
                return JsonResponse({"status": "successful", "url": s3_url})
            else:
                logger.warning(f"Fallo al obtener URL de S3 con mixmonFileName: {mixmon_file_name}. Procediendo con fallback.")
        
        recording_key = payload.get('uniqueID') or payload.get('queueCallManagerID')

        if not recording_key:
            logger.error("uniqueID no proporcionado en createRecordingURL.")
            return JsonResponse({"status": "error", "description": "Missing uniqueID"}, status=400)

        url = get_sharpen_audio_url(recording_key)
        if url:
            return JsonResponse({"status": "successful", "url": url})
        return JsonResponse({"status": "error", "description": "Sharpen audio URL request failed"}, status=500)

    # El método _handle_sql_query ya fue integrado directamente en `post` para manejar el `full_payload_for_forward`

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
