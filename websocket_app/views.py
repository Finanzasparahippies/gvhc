#websocket_app/views,py
from django.http import JsonResponse
import psutil
from websocket_app.fetch_script import fetch_calls_on_hold_data
import asyncio # Necesario para ejecutar funciones asíncronas en vistas síncronas

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
    # Ejecuta la función asíncrona en el bucle de eventos actual
    data = asyncio.run(fetch_calls_on_hold_data())
    return JsonResponse(data)