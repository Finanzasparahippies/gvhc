#websocket_app/views,py
from django.http import JsonResponse
import psutil
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

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

def get_live_queue_status_api(request):
    """
    API endpoint para obtener el estado actual de la cola en vivo.
    """
    # Aquí obtendrías tus datos de LiveQueueStatusData.
    # Esto es solo un ejemplo; ajusta la lógica para que coincida con tus datos reales.
    live_queue_data = [
        {"QueueName": "Ventas", "commType": "llamadas", "intervals": "0-15s"},
        {"QueueName": "Soporte", "commType": "chats", "intervals": "15-30s"},
        # ... más datos
    ]
    # Si tus datos vienen de un serializer, puedes serializarlos aquí:
    # from .serializers import LiveQueueStatusSerializer
    # live_queue_data = LiveQueueStatusSerializer(QueueStatus.objects.all(), many=True).data

    return JsonResponse({
        "getLiveQueueStatusData": live_queue_data
    })