# dashboards/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import News
from .serializers import NewsSerializer

@api_view(['GET'])
@permission_classes([AllowAny])
def news_list(request):
    news_items = News.objects.all().order_by('-published_at')
    serializer = NewsSerializer(news_items, many=True)
    return Response(serializer.data)
