import openpyxl
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Q, F, Func, Value
from django.db.models.functions import Concat
from django.contrib.postgres.fields import ArrayField
from .models import Answer, Faq, Event, Step, Department
from .serializers import AnswerSerializer, FaqSerializer, EventSerializer
from pprint import pprint


class AnswerViewSet(viewsets.ModelViewSet):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer

class FaqViewSet(viewsets.ModelViewSet):
    queryset = Faq.objects.all()
    serializer_class = FaqSerializer

@api_view(['GET'])
def search_faqs(request):
    query = request.GET.get('query', '').strip()
    if not query:
        return Response({'results': []}, status=200)

    try:
        faqs = Faq.objects.filter(
            # Q(question__icontains=query) |
            # Q(keywords__icontains=query) |
            Q(answers__answer_text__icontains=query) 
        ).distinct()

        serializer = FaqSerializer(faqs, many=True)

        pprint(serializer.data)       
        
        return Response({'results': serializer.data}, status=200)

    except Exception as e:
        # Captura errores y devuélvelos en la respuesta
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def get_departments(request):
    # Puedes obtener los tipos de cola únicos de tus FAQs existentes
    queue_types = Faq.objects.values_list('queue_type', flat=True).distinct()
    # O si prefieres usar las categorías como grupos principales
    department = Department.objects.values_list('name', flat=True).distinct()

    # Decide cuál usarás como "departamento" principal para el agrupamiento
    # Por ejemplo, si usas queue_type:
    departments_data = [{'id': qt, 'name': dict(Faq.QUEUE_TYPES).get(qt, qt)} for qt in queue_types]
    return Response(departments_data)

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

