from django.db import models

class ReporteLlamadas(models.Model):
    fecha_reporte = models.DateField()
    total_llamadas = models.IntegerField()
    llamadas_atendidas = models.IntegerField()
    tmo = models.DurationField()
    archivo_origen = models.FileField(upload_to='reportes/')

    creado = models.DateTimeField(auto_now_add=True)