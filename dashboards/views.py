import requests
import json
import os
import logging
from django.http import StreamingHttpResponse, JsonResponse
from rest_framework.views import APIView, View
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

# Create your views here.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProxyRecordingView(View):
    def get(self, request, recording_key):
        sharpen_url = f"https://api-current.iz1.sharpen.cx/V2/voice/callRec/{recording_key}"
        r = requests.get(sharpen_url, stream=True)

        if r.status_code != 200:
            return JsonResponse({"error": "No se pudo obtener el audio"}, status=502)

        response = StreamingHttpResponse(r.iter_content(chunk_size=8192), content_type=r.headers['Content-Type'])
        response['Content-Disposition'] = 'inline; filename="audio.mp3"'
        return response

class SharpenApiProxyView(APIView):
    permission_classes = [AllowAny] 

    def post(self, request, *args, **kwargs ):
        print(request.data)

        base_query = request.data.get('q')
        if not base_query:
            return Response({"error": "La consulta 'q' es requerida."}, status=400)

        cKey1 = os.getenv('SHARPEN_CKEY1')
        cKey2 = os.getenv('SHARPEN_CKEY2')
        uKey = os.getenv('SHARPEN_UKEY')

        print(f"Loaded cKey1: {cKey1}, cKey2: {cKey2}, uKey: {uKey}") 
        logger.debug(f"Loaded cKey1: {cKey1}, cKey2: {cKey2}, uKey: {uKey}")


        if not cKey1 or not cKey2 or not uKey:
            logger.error(f"Error: SHARPEN_CKEY1={cKey1}, SHARPEN_CKEY2={cKey2}, SHARPEN_UKEY={uKey} no están configuradas correctamente en el entorno.")
            return Response({"error": "Configuración del servidor incompleta."}, status=500)
        
        external_api_url = 'https://api-current.iz1.sharpen.cx/V2/query/'
        
        method_from_client = request.data.get('method', '')

        internal_payload = {
            "cKey1": cKey1,
            "cKey2": cKey2,
            "uKey": uKey,
            "endpoint": "V2/query/",
            "q": base_query,
            "pKey2": "",
            "connection.database": "",
            "connection.password": "",
            "connection.username": "",
            "connection.host": "",
            "connection": "",
            "crm-userID": "",
            "distinctColumn": "",
            "params": "", 
            "method": method_from_client, 
            "table": "",
            "database": "",
            "server": "",
            "append": "",
        }

        try:
                logger.info(f"Enviando petición a Sharpen: {internal_payload}")
                response = requests.post(
                    external_api_url,
                    data=internal_payload,
                    # headers={'Content-Type': 'application/json'},
                    timeout=30
                )

                print(f"response: {response.text}")
                logger.info(f"Respuesta cruda de Sharpen (Status: {response.status_code}): {response.text}")
                
                # Lanza un error para códigos 4xx o 5xx
                response.raise_for_status() 
                try:
                    result = response.json()

                    if result.get('status') == 'Complete':
                        logger.info("¡ÉXITO! Conexión y consulta a la base de datos de Sharpen realizadas correctamente.")
                    else:
                        logger.warning(f"La API de Sharpen respondió, pero el estado no fue 'Complete'. Estado recibido: {result.get('status')}")

                    return Response(result) 
                except json.JSONDecodeError:
                    logger.warning("Respuesta con Content-Type JSON pero no se pudo parsear.")
                    return Response({
                        "error": "La respuesta no es JSON", 
                        "raw_response": response.text
                        }, status=502)
                
        except requests.exceptions.HTTPError as e:
            logger.error(f"Error HTTP de la API de Sharpen: {e.response.status_code} - {e.response.text}")
            return Response({"error": "Error al comunicarse con la API externa.", "details": e.response.text}, status=e.response.status_code)
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión con la API de Sharpen: {e}")
            return Response({"error": "No se pudo conectar con la API externa."}, status=503) # Service Unavailable
        except Exception as e:
            logger.error(f"Error inesperado en el proxy: {e}")
            return Response({"error": "Ocurrió un error inesperado en el servidor."}, status=500)


class SharpenApiGenericProxyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        # El frontend ahora nos dirá a qué endpoint de Sharpen llamar
        # y qué datos enviar.
        sharpen_endpoint = request.data.get('endpoint')
        sharpen_payload = request.data.get('payload', {})

        if not sharpen_endpoint or not isinstance(sharpen_payload, dict):
            return Response({"error": "Se requiere 'endpoint' y 'payload' en la petición."}, status=400)

        # Carga las claves secretas desde el entorno
        cKey1 = os.getenv('SHARPEN_CKEY1')
        cKey2 = os.getenv('SHARPEN_CKEY2')
        uKey = os.getenv('SHARPEN_UKEY')

        if not all([cKey1, cKey2, uKey]):
            logger.error("Error: Las claves de Sharpen no están configuradas en el entorno.")
            return Response({"error": "Configuración del servidor incompleta."}, status=500)
        
        # Construye la URL completa para la API de Sharpen
        external_api_url = f"https://api-current.iz1.sharpen.cx/{sharpen_endpoint}/"

        # Inyecta las claves secretas en el payload que viene del cliente.
        # Esto es seguro porque las claves nunca salen de tu backend.
        full_payload = {
            "cKey1": cKey1,
            "cKey2": cKey2,
            "uKey": uKey,
            "recordID": "", # Si siempre es vacío o no lo tienes en el frontend
            "pKey2": "",
            "fileName": "",
            "make": "",
            "callTag": "",
            "clickToCallID": "",
            "callRecordID": "",
            **sharpen_payload  # Combina las claves con el resto del payload
        }

        try:
            logger.info(f"Enviando petición a Sharpen URL: {external_api_url}")
            logger.info(f"Enviando payload a Sharpen: {full_payload}")

            response = requests.post(
                external_api_url,
                data=full_payload, # Usamos data para que se envíe como form-data
                timeout=30
            )
            
            response.raise_for_status() # Lanza error para respuestas 4xx/5xx

            # Intenta devolver la respuesta como JSON, si no, como texto.
            try:
                return Response(response.json())
            except json.JSONDecodeError:
                logger.warning("La respuesta de Sharpen no es un JSON válido. Devolviendo respuesta como texto plano.")
                return Response({"raw_response": response.text}) # Devolvemos el texto crudo dentro de un JSON con una clave específica para que el frontend lo maneje.

        except requests.exceptions.HTTPError as e:
            logger.error(f"Error HTTP de la API de Sharpen: {e.response.status_code} - {e.response.text}")
            return Response({"error": "Error al comunicarse con la API externa.", "details": e.response.text}, status=e.response.status_code)
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión con la API de Sharpen: {e}")
            return Response({"error": "No se pudo conectar con la API externa."}, status=503)
        except Exception as e:
            logger.error(f"Error inesperado en el proxy: {e}")
            return Response({"error": "Ocurrió un error inesperado en el servidor."}, status=500)
