from django.db import models

class ReporteLlamadas(models.Model):
    fecha_reporte = models.DateField()
    total_llamadas = models.IntegerField()
    llamadas_atendidas = models.IntegerField()
    tmo = models.DurationField()
    archivo_origen = models.FileField(upload_to='reportes/')

    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
            return f"Reporte {self.fecha_reporte} - Llamadas atendidas: {self.llamadas_atendidas}"