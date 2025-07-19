# dashboards/views_quotes.py

import requests
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny  # si no requiere login

@api_view(['GET'])
@permission_classes([AllowAny])
def fetch_quote(request):
    try:
        res = requests.get("https://zenquotes.io/api/random", timeout=5)
        data = res.json()
        return Response(data[0])  # solo devolvemos el primer elemento
    except Exception as e:
        return Response({'error': str(e)}, status=500)
