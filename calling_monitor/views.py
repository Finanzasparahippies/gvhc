#calling_monitor/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import CallAnalysis
from .utils.transcriber import transcribe_audio_filelike_no_disk, get_vosk_model_path # Import get_vosk_model_path too
from .utils.analyzer import extract_information
import json
from io import BytesIO
import requests 
import tempfile
import logging
logger = logging.getLogger(__name__)

@csrf_exempt
def analyze_remote_audio(request):
    """
    Analiza directamente el audio remoto de Sharpen, sin necesidad de subirlo.
    """
    logger.debug("Received request for analyze_remote_audio")
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        data = json.loads(request.body)
        audio_url = data.get("audioUrl") # Ahora esperamos la URL directa
        unique_id = data.get("uniqueID") # Mantén el uniqueID para asociar con la llamada
        lang = data.get("lang", "es") 

        logger.debug(f"Attempting to analyze audio from URL: {audio_url}, Unique ID: {unique_id}")

        if not audio_url or not unique_id:
            logger.error(f"Missing parameters: audioUrl={audio_url}, uniqueID={unique_id}")
            return JsonResponse({"error": "Faltan parámetros (audioUrl o uniqueID)."}, status=400)

        # Descarga el audio directamente desde la URL proporcionada
        # Aumenta el timeout si los archivos de audio son grandes
        response = requests.get(audio_url, timeout=60) 
        response.raise_for_status() # Lanza una excepción para errores HTTP (4xx o 5xx)
        logger.debug(f"Successfully downloaded audio from {audio_url}")

        audio_data = BytesIO(response.content)

        # Transcribe el audio desde el objeto BytesIO
        transcript = transcribe_audio_filelike_no_disk(audio_data, lang=lang) 
        logger.debug(f"Transcription successful: {transcript[:100]}...")

        analysis = extract_information(transcript)
        logger.debug(f"Analysis successful: {analysis}")

        # Guarda el análisis en la base de datos
        # Asegúrate de que tu modelo CallAnalysis tiene un campo 'unique_id'
        instance = CallAnalysis.objects.create(
            audio_file=None,  # El audio no se sube localmente, solo se procesa desde la URL
            transcript=transcript,
            motives=analysis["motivos"],
            agent_actions=analysis["acciones_agente"],
            unique_id=unique_id, # Guarda el uniqueID para referencia
            language_used=lang # You might want to add this field to your CallAnalysis model
        )
        logger.info(f"CallAnalysis instance created with ID: {instance.id}")

        return JsonResponse({
            "id": instance.id,
            "transcript": transcript,
            "analysis": analysis,
            "message": "Audio analizado exitosamente.",
            "language_used": lang # Return which language model was used
        })

    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading audio from URL {audio_url}: {str(e)}", exc_info=True)
        return JsonResponse({"error": f"Error descargando audio desde la URL: {str(e)}"}, status=500)
    except Exception as e:
        logger.error(f"Error during transcription or analysis for {unique_id}: {str(e)}", exc_info=True)
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
            transcript = transcribe_audio(instance.audio_file.path)
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


