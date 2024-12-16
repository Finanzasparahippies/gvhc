from django.db import models
from django.conf import settings
from rest_framework import serializers
from .models import Answer, AnswerConnection, Faq, Event, Step, Slide


class AnswerConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerConnection
        fields = ['to_answer', 'condition']

class StepSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    class Meta:
        model = Step
        fields = ['number', 'text', 'image_url']

    def get_image_url(self, obj):
        if obj.image:  # Asegúrate de que la imagen existe
            try:
                return obj.image.url
            except Exception as e:
                print(f"Error al obtener la URL de la imagen: {e}")
                return None
        return None

class AnswerSerializer(serializers.ModelSerializer):
    steps = StepSerializer(many=True)  # Incluye todos los datos de Step
    connections = AnswerConnectionSerializer(source='from_connections', many=True, required=False)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Answer
        fields = ['id', 'answer_text', 'template', 'image', 'steps', 'relevance', 'connections', 'image_url', 'node_type']

    def get_image_url(self, obj):
        if obj.image:
            # Retorna la URL directa de Cloudinary
            return obj.image.url
        return None

class SlideSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slide
        fields = ['id', 'faq', 'question', 'left', 'right', 'up', 'down']

class FaqSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True)
    slides = SlideSerializer(many=True, read_only=True)
    popularity = serializers.SerializerMethodField()
    response_type = serializers.SerializerMethodField()  
    category = serializers.SerializerMethodField()

    class Meta:
        model = Faq
        fields = ['id', 'question', 'category', 'answers', 'created_at', 'slides', 'popularity', 'response_type', 'keywords']

    def get_popularity(self, obj):
        # Calcula la popularidad en base a la relevancia acumulada de las respuestas
        return obj.answers.aggregate(total_relevance=models.Sum('relevance')).get('total_relevance') or 0
    
    def get_response_type(self, obj):
        return obj.response_type.type_name if obj.response_type else 'unknown'
    
    def get_category(self, obj):
        return obj.category.name if obj.category else 'unknown'

    
class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = '__all__'

