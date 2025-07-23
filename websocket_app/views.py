#websocket_app/views,py
from django.http import JsonResponse


def cors_test(request):
    return JsonResponse({"message": "CORS works!"})