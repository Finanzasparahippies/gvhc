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
    excel_content = serializers.SerializerMethodField()

    class Meta:
        model = Step
        fields = ['number', 'text', 'image_url', 'excel_content']

    def get_excel_content(self, obj):
        if not obj.excel_file:
            return None
        try:
            from openpyxl import load_workbook
            workbook = load_workbook(obj.excel_file)
            sheet = workbook.active
            content = []
            for row in sheet.iter_rows(min_row=2, values_only=True):  # Salta encabezados
                content.append(row)
            return content
        except Exception as e:
            return str(e)        

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
    queue_type = serializers.SerializerMethodField()

    class Meta:
        model = Faq
        fields = '__all__'

    def get_popularity(self, obj):
        # Calcula la popularidad en base a la relevancia acumulada de las respuestas
        return obj.answers.aggregate(total_relevance=models.Sum('relevance')).get('total_relevance') or 0
    
    def get_response_type(self, obj):
        return obj.response_type.type_name if obj.response_type else 'unknown'
    
    def get_category(self, obj):
        return obj.category.name if obj.category else 'unknown'

    def get_queue_type(self, obj):
        print(f"Queue Type: {obj.queue_type}")  # Para ver si se está llamando correctamente
        return obj.get_queue_type_display()

    
class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = '__all__'

