from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Q
from .models import Answer, Faq, Event
from .serializers import AnswerSerializer, FaqSerializer, EventSerializer

class AnswerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer

class FaqViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Faq.objects.select_related('category').prefetch_related('answers__steps', 'slides')
    serializer_class = FaqSerializer

@api_view(['GET'])
def search_faqs(request):
    query = request.GET.get('query', '')
    if query:
        faqs = Faq.objects.filter(
            Q(question__icontains=query) | Q(keywords__icontains=query)
        ).distinct()
        serializer = FaqSerializer(faqs, many=True)
        return Response(serializer.data)
    return Response([])

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer