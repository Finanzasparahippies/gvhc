from django.shortcuts import render
from django.http import JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from .utils.procesamiento import procesar_archivo
from .models import ReporteLlamadas
from datetime import datetime

@csrf_exempt
def procesar_reporte(request):
    if 'archivo' not in request.FILES:
        return JsonResponse({'error': 'No se proporcionó ningún archivo'}, status=400)
    
    if request.method == 'POST' and request.FILES['archivo']:
        archivo = request.FILES['archivo']
        print(f"Archivo recibido: {archivo.name}")
        # Suponiendo que el archivo es Excel
        try:
            resultados, archivo_generado = procesar_archivo(archivo)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
        
        fecha_reporte = request.POST.get('fecha', None)
        print(f"Fecha recibida: {fecha_reporte}")
        if  fecha_reporte:
            try:
                fecha_reporte = datetime.strptime(fecha_reporte, '%Y-%m-%d').date()
            except ValueError as e:
                return JsonResponse({'error': f"Error al procesar la fecha: {str(e)}"}, status=400)
            
        ReporteLlamadas.objects.create(
            fecha_reporte=fecha_reporte,
            total_llamadas=resultados["Total llamadas"],
            llamadas_atendidas=resultados["Total llamadas atendidas"],
            tmo=resultados["TMO"],
            archivo_origen=archivo
        )

        # Enviar el archivo procesado como respuesta para descarga
        response = FileResponse(archivo_generado, as_attachment=True, filename='reporte_procesado.xlsx')
        return response

    return JsonResponse({'error': 'Método no permitido o datos incompletos'}, status=400)
