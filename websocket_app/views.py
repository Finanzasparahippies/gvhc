#websocket_app/views,py
from django.http import JsonResponse
import psutil
from .fetch_script import fetch_calls_on_hold_data
import asyncio # Necesario para ejecutar funciones asíncronas en vistas síncronas
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
    permission_classes = [IsAuthenticated] # Asegúrate de que solo usuarios autenticados puedan acceder

    def get(self, request, *args, **kwargs):
        # Aquí va la lógica para obtener tus datos de LiveQueueStatus
        # Esto es un placeholder, ajústalo a tu estructura de datos real.
        # Podrías consultar una base de datos, un caché, etc.
        sample_data = [
            {"QueueName": "Ventas Online", "commType": "Llamadas", "intervals": "0-10s"},
            {"QueueName": "Soporte Técnico", "commType": "Chats", "intervals": "10-30s"},
            {"QueueName": "Reclamos", "commType": "Llamadas", "intervals": "30-60s"},
        ]
        # Si usas un serializer:
        # queryset = LiveQueueStatusModel.objects.all()
        # serializer = LiveQueueStatusSerializer(queryset, many=True)
        # return JsonResponse({"getLiveQueueStatusData": serializer.data})

        return JsonResponse({"getLiveQueueStatusData": sample_data})

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