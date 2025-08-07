#calling_monitor/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import CallAnalysis
import json
import os # Import the os module
from io import BytesIO
import requests 
import tempfile
import logging
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from dashboards.views import get_sharpen_audio_url
from .utils.audio_helper import get_audio_from_url # Importa la nueva función
from .utils.transcriber import transcribe_audio_filelike_no_disk # Import get_vosk_model_path too
from .utils.analyzer import extract_information
from bs4 import BeautifulSoup
import language_tool_python
from urllib.parse import urljoin, unquote, urlparse, urlunparse # Asegúrate de importar unquote

logger = logging.getLogger(__name__)

@csrf_exempt
def analyze_remote_audio(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        data = json.loads(request.body)
        audio_url = data.get("audioUrl")
        unique_id = data.get("uniqueID")
        lang = data.get("lang", "es")

        logger.debug(f"Intentando analizar audio desde URL: {audio_url}, Unique ID: {unique_id}, Lang: {lang}")

        if not audio_url or not unique_id:
            logger.error(f"Faltan parámetros: audioUrl={audio_url}, uniqueID={unique_id}")
            return JsonResponse({"error": "Faltan parámetros (audioUrl o uniqueID)."}, status=400)

        audio_data = get_audio_from_url(audio_url)

        transcription_result = transcribe_audio_filelike_no_disk(audio_data, lang=lang)
        logger.debug(f"Tipo de transcripción: {type(transcription_result)}, Valor: {transcription_result}")
        if isinstance(transcription_result, tuple):
            transcript = transcription_result[0]
        else:
            transcript = transcription_result
        logger.info(f"Transcripción completada para {unique_id}.")        # LLAMADA ACTUALIZADA a extract_information
        analysis = extract_information(transcript, lang=lang)

        instance = CallAnalysis.objects.create(
            audio_file=None,
            transcript=transcript,
            # Ahora guardamos los nuevos campos
            high_risk_warnings=json.dumps(analysis["high_risk_warnings"]), # Guarda como JSON string
            call_motives=json.dumps(analysis["call_motives"]), # Guarda como JSON string
            # Los siguientes campos podrían ser redundantes si "motivos" y "acciones_agente"
            # son ahora cubiertos por high_risk_warnings y call_motives.
            # Decide si aún los necesitas o si el nuevo análisis los reemplaza.
            motives=json.dumps(analysis.get("motivos", [])), # Usar .get para evitar KeyError si lo eliminas
            agent_actions=json.dumps(analysis.get("acciones_agente", [])),
            unique_id=unique_id,
            language_used=lang
        )
        logger.info(f"Instancia CallAnalysis creada con ID: {instance.id}")

        return JsonResponse({
            "id": instance.id,
            "transcript": transcript,
            "analysis": {
                "high_risk_warnings": analysis["high_risk_warnings"],
                "call_motives": analysis["call_motives"],
                "motivos": analysis.get("motivos", []),
                "agent_actions": analysis.get("acciones_agente", []),
            },
            "message": "Audio analizado exitosamente.",
            "language_used": lang
        })

    except requests.exceptions.RequestException as e:
        logger.error(f"Error descargando audio desde URL {audio_url}: {str(e)}", exc_info=True)
        return JsonResponse({"error": f"Error descargando audio desde la URL: {str(e)}"}, status=500)
    except Exception as e:
        logger.error(f"Error durante la transcripción o análisis para {unique_id}: {str(e)}", exc_info=True)
        return JsonResponse({"error": f"Error durante la transcripción o análisis: {str(e)}"}, status=500)

# Create your views here.
@csrf_exempt
def process_call(request):
    if request.method == "POST":
        audio = request.FILES.get("audio")
        if not audio:
            return JsonResponse({"error": "Archivo de audio no enviado"}, status=400)

        instance = CallAnalysis.objects.create(audio_file=audio)
        try:
            transcript = transcribe_audio_filelike_no_disk(instance.audio_file.path)
            analysis = extract_information(transcript)

            instance.transcript = transcript
            instance.motives = analysis["motivos"]
            instance.agent_actions = analysis["acciones_agente"]
            instance.save()

            return JsonResponse({
                "transcript": transcript,
                "analysis": analysis
            })

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Método no permitido"}, status=405)

@csrf_exempt
def grammar_correction2(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user_text = data.get('text')

        if user_text:
            # Configurar LanguageTool con opciones avanzadas
            tool = language_tool_python.LanguageTool('en-US', config={
                'maxTextLength': 500, 
                'maxErrorsPerWordRate': 0.5,
                'maxSpellingSuggestions': 3,  # Solo 3 sugerencias de ortografía por error
                'cacheSize': 20,  # Tamaño de caché
                'cacheTTLSeconds': 300,  # Tiempo de vida de caché: 5 minutos
                'pipelineCaching': True,  # Habilita caché de pipelines
                'pipelineExpireTimeInSeconds': 600,  # Cache de pipelines expira en 10 minutos
                })
            tool.disable_spellchecking = False
            tool.picky = True  # Activa picky mode para sugerencias detalladas

            # Realizar la corrección
            matches = tool.check(user_text)
            corrected_text = language_tool_python.utils.correct(user_text, matches)

            # Crear una respuesta detallada con sugerencias de corrección
            suggestions = [
                {
                    "error": match.context,
                    "suggestions": match.replacements,
                    "rule": match.ruleId
                }
                for match in matches
            ]
            
            return JsonResponse({"corrected_text": corrected_text, "suggestions": suggestions})
        else:
            return JsonResponse({"error": "No text provided"}, status=400)
    return JsonResponse({"error": "Invalid request method"}, status=405)


@api_view(['POST'])
@permission_classes([AllowAny])  # 👈 Esto es lo que necesitas
def analyze_sharpen_audio(request):
    """
    Endpoint que analiza audio de Sharpen directamente.
    Espera `mixmonFileName`, `uniqueID` y opcionalmente `lang`.
    """
    mixmon_file_name = request.data.get("mixmonFileName")
    unique_id = request.data.get("uniqueID")
    lang = request.data.get("lang", "en")

    if not mixmon_file_name or not unique_id:
        logger.error(f"Faltan parámetros en la solicitud. mixmonFileName: {mixmon_file_name}, uniqueID: {unique_id}") # <-- Mejora el log aquí
        return Response({"error": "mixmonFileName y uniqueID son requeridos"}, status=400)

    try:
        # 1. Obtener la URL firmada de Sharpen (lógica específica de esta vista)
        sharpen_proxy_url = get_sharpen_audio_url(mixmon_file_name, unique_id)
        if not sharpen_proxy_url:
            logger.error(f"No se pudo obtener la URL del proxy de Sharpen para {unique_id}. Sharpen API no devolvió URL.")
            return Response({"error": "No se pudo obtener la URL de audio de Sharpen"}, status=500)
        
        logger.info(f"URL de proxy de Sharpen obtenida para {unique_id}: {sharpen_proxy_url}")
        
        # 2. Usar la función unificada para descargar y resolver la URL
        audio_data = get_audio_from_url(sharpen_proxy_url)

        # 3. El resto de la lógica de transcripción y análisis es la misma
        logger.info(f"Iniciando transcripción para {unique_id}...")
        transcription_result = transcribe_audio_filelike_no_disk(audio_data, lang)
        if isinstance(transcription_result, tuple):
            transcription_text = transcription_result[0]
        else:
            transcription_text = transcription_result
            
        logger.info(f"Transcripción completada para {unique_id}.")
        
        analysis = extract_information(transcription_text, lang=lang)
        logger.info(f"Análisis Spacy completado para {unique_id}.")

        instance = CallAnalysis.objects.create(
            audio_file=None,
            transcript=transcription_text,
            high_risk_warnings=json.dumps(analysis.get("high_risk_warnings", [])),
            call_motives=json.dumps(analysis.get("call_motives", [])),
            motives=json.dumps(analysis.get("motivos", [])),
            agent_actions=json.dumps(analysis.get("acciones_agente", [])),
            unique_id=unique_id,
            language_used=lang,
        )
        logger.info(f"Instancia CallAnalysis creada para audio de Sharpen con ID: {instance.id}")

        return Response({
            "status": "success",
            "transcription": transcription_text,
            "uniqueID": unique_id,
            "analysis": analysis,
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error durante el proceso de análisis para {unique_id}: {e}", exc_info=True)
        return Response({"error": f"Ocurrió un error al procesar la URL: {str(e)}"}, status=500)
