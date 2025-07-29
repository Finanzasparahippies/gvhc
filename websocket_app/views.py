#websocket_app/views,py
from django.http import JsonResponse
import psutil
from .fetch_script import fetch_calls_on_hold_data, fetch_live_queue_status_data
from asgiref.sync import async_to_sync 
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

async def get_calls_on_hold_from_sharpen(request):
    """
    Obtiene los datos de las llamadas en espera consultando la API de Sharpen
    y los devuelve como una respuesta JSON.
    """
    try:
        data = await fetch_calls_on_hold_data()
        # Sharpen devuelve un objeto con 'getCallsOnHoldData'
        # Asegúrate de que el formato de la respuesta sea consistente con lo que espera el frontend
        if data and "getCallsOnHoldData" in data and isinstance(data["getCallsOnHoldData"], list):
            # Aquí, el 'payload' que estás enviando por WebSocket es `{ "getCallsOnHoldData": [...] }`
            # Así que el endpoint REST también debería coincidir con eso para consistencia.
            return JsonResponse({"getCallsOnHoldData": data["getCallsOnHoldData"]})
        else:
            # Si Sharpen no devolvió datos válidos, o el formato es incorrecto
            return JsonResponse({"getCallsOnHoldData": []}, status=200) # Devolver un array vacío pero con 200 OK
    except Exception as e:
        print(f"Error al obtener llamadas en espera de Sharpen: {e}")
        return JsonResponse({"error": "Error al obtener datos de llamadas en espera"}, status=500)

class LiveQueueStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs): # Haz el método 'get' asíncrono
        try:
            data = async_to_sync(fetch_live_queue_status_data)() 
            if data and "getLiveQueueStatusData" in data and isinstance(data["getLiveQueueStatusData"], list):
                return JsonResponse({"getLiveQueueStatusData": data["getLiveQueueStatusData"]})
            else:
                return JsonResponse({"getLiveQueueStatusData": []}, status=200)
        except Exception as e:
            print(f"Error al obtener estado de cola en vivo de Sharpen: {e}")
            return JsonResponse({"error": "Error al obtener datos de estado de cola en vivo"}, status=500)

def cors_test(request):
    return JsonResponse({"message": "CORS works!"})

def system_metrics_view(request):
    memory = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=0.5)
    return JsonResponse({
        "memory_used_mb": round(memory.used / (1024 ** 2), 2),
        "memory_percent": memory.percent,
        "cpu_percent": cpu
    })