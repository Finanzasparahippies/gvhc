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
from websocket_app.fetch_script import _call_sharpen_api_async # 👈 Importamos la función "cerebro"
from asgiref.sync import async_to_sync
from rest_framework import status # Add this import if you're using status.HTTP_xxx_REQUEST

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
    """
    Esta vista ahora actúa como un simple delegado.
    Toda la lógica de negocio vive en `call_sharpen_api_service`.
    """
    def post(self, request):
        endpoint = request.data.get('endpoint')
        payload = request.data.get('payload')

        if not endpoint or not isinstance(payload, dict):
            return Response(
                {"status": "error", "description": "Missing 'endpoint' or invalid 'payload'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Llama a la función de servicio asíncrona desde este contexto síncrono
        result = async_to_sync(_call_sharpen_api_async)(endpoint, payload)

        # Maneja la respuesta del servicio
        if result and "error" not in result:
            return Response(result, status=status.HTTP_200_OK)
        else:
            # Devuelve el código de estado y mensaje de error que el servicio reportó
            status_code = result.get("status_code", 500) if result else 500
            error_desc = result.get("error", "Failed to fetch data from the external API.") if result else "Internal Server Error"
            return Response(
                {"status": "error", "description": error_desc},
                status=status_code
            )
