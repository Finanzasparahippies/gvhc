import requests
import json
import os
import logging
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

# Create your views here.
logger = logging.getLogger(__name__)

class SharpenApiProxyView(APIView):
    permission_classes = [AllowAny] # Asegura que solo usuarios logueados puedan usarla

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
        
        external_api_url = 'https://api-current.iz1.sharpen.cx/V2/query'
        # external_api_url = 'https://api-current.iz1.sharpen.cx/V2/queues/getQueueCDR'

        param001_val = request.data.get('param001')
        param002_val = request.data.get('param002')
        param003_val = request.data.get('param003')
        method_from_client = request.data.get('method', '')

        params_dict = {
            ":param001": param001_val,
            ":param002": param002_val,
            ":param003": param003_val
        }

        # final_query = final_query.replace('crm-companyID', '`crm-companyID`')

        # payload = {
        #     "method": method_from_client,
        #     "q": final_query,
        #     "cKey1": cKey1,
        #     "cKey2": cKey2,
        #     "uKey": uKey
        # }

        internal_payload = {
            "cKey1": cKey1,
            "cKey2": cKey2,
            "uKey": uKey,
            "q": base_query,
            # Añade todos los parámetros adicionales que Sharpen espera,
            # incluso si están vacíos. Esto es crucial si la API es estricta.
            "pKey2": "",
            "connection.database": "",
            "connection.password": "",
            "connection.username": "",
            "connection.host": "",
            "connection": "",
            "crm-userID": "",
            "distinctColumn": "",
            "params": json.dumps(params_dict), # <-- ¡Aquí está la cadena JSON de parámetros!
            "method": method_from_client, # El ejemplo de PHP no lo incluye, pero tu doc dice "method: query"
            "table": "",
            "database": "",
            "server": "",
            "append": "",
        }

        # final_payload = {'formdata': json.dumps(internal_payload)}


        try:
                logger.info(f"Enviando petición a Sharpen: {internal_payload}")
                response = requests.post(
                    external_api_url,
                    json=internal_payload,
                    # headers={'Content-Type': 'application/json'},
                    timeout=30
                )

                print(f"response: {response.text}")
                logger.info(f"Respuesta cruda de Sharpen (Status: {response.status_code}): {response.text}")
                
                # Lanza un error para códigos 4xx o 5xx
                response.raise_for_status() 
                try:
                    result = response.json()
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

