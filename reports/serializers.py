from rest_framework import serializers
from .models import ReporteLlamadas

class ReporteLlamadasSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReporteLlamadas
        fields = ['fecha_reporte', 'total_llamadas', 'llamadas_atendidas', 'tmo', 'archivo_origen']
