#websocket_app/views,py
from django.http import JsonResponse
import psutil
from .fetch_script import fetch_calls_on_hold_data
import asyncio


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


def get_calls_on_hold(request):
    data = asyncio.run(fetch_calls_on_hold_data())
    return JsonResponse(data)