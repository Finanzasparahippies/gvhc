#calling_monitor/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import CallAnalysis
from .utils.transcriber import transcribe_audio_filelike_no_disk, get_vosk_model_path # Import get_vosk_model_path too
from .utils.analyzer import extract_information
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
from .utils.audio_helper import download_audio_as_filelike
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

        # ... (lógica de descarga de audio, sin cambios)
        response = requests.get(audio_url, timeout=60)
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "")
        logger.debug(f"Content-Type de la respuesta inicial: {content_type}")

        if "text/html" in content_type.lower():
            soup = BeautifulSoup(response.text, "html.parser")
            source_tag = soup.find("source")
            if source_tag and source_tag.has_attr("src"):
                potential_audio_url = source_tag["src"]
                audio_url_real = urljoin(audio_url, potential_audio_url)
                logger.debug(f"URL real extraída del HTML (o construida): {audio_url_real}")
                response_audio = requests.get(audio_url_real, timeout=60)
                response_audio.raise_for_status()
                audio_data = BytesIO(response_audio.content)
            else:
                logger.error("No se encontró la etiqueta <source> con atributo 'src' en el HTML")
                return JsonResponse({"error": "No se pudo extraer URL de audio desde la página HTML"}, status=500)
        else:
            audio_data = BytesIO(response.content)

        transcript = transcribe_audio_filelike_no_disk(audio_data, lang=lang)
        logger.debug(f"Tipo de transcripción: {type(transcription)}, Valor: {transcription}") # Añade esta línea
        logger.info(f"Transcripción completada para {unique_id}.")
        # LLAMADA ACTUALIZADA a extract_information
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
    lang = request.data.get("lang", "es")

    if not mixmon_file_name or not unique_id:
        logger.error(f"Faltan parámetros en la solicitud. mixmonFileName: {mixmon_file_name}, uniqueID: {unique_id}") # <-- Mejora el log aquí
        return Response({"error": "mixmonFileName y uniqueID son requeridos"}, status=400)

    # 1. Obtener la URL firmada de Sharpen
    sharpen_proxy_url = get_sharpen_audio_url(mixmon_file_name, unique_id)
    if not sharpen_proxy_url:
        logger.error(f"No se pudo obtener la URL del proxy de Sharpen para {unique_id}. Sharpen API no devolvió URL.")
        return Response({"error": "No se pudo obtener la URL de audio de Sharpen"}, status=500)
    
    logger.info(f"URL de proxy de Sharpen obtenida para {unique_id}: {sharpen_proxy_url}")
    current_url_to_fetch = sharpen_proxy_url
    audio_data = None
    max_redirects_html = 3 # Limitar las redirecciones a través de HTML para evitar bucles infinitos

    for i in range(max_redirects_html):
        try:
            logger.info(f"Intentando obtener contenido de: {current_url_to_fetch} (Intento {i+1})")
            response = requests.get(current_url_to_fetch, timeout=60)
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "").lower()
            logger.debug(f"Content-Type recibido de '{current_url_to_fetch}': '{content_type}'")

            if "text/html" in content_type:
                logger.info(f"URL '{current_url_to_fetch}' devolvió HTML. Buscando la URL de audio real con BeautifulSoup.")
                html_content = response.text
                logger.debug(f"Contenido HTML (primeros 500 chars): {html_content[:500]}")
                soup = BeautifulSoup(html_content, "html.parser")

                extracted_url = None
                source_tag = soup.find("source")
                audio_tag = soup.find("audio")
                # Si no se encuentra <source>, intenta buscar el src directamente en <audio>
                if source_tag and source_tag.has_attr("src"):
                    extracted_url = source_tag["src"]
                    logger.info(f"URL extraída de <source src>: {extracted_url}")
                elif audio_tag and audio_tag.has_attr("src"):
                    extracted_url = audio_tag["src"]
                    logger.info(f"URL extraída de <audio src>: {extracted_url}")
                else:
                    logger.error(f"HTML recibido de '{current_url_to_fetch}', pero no se encontró la etiqueta <source> ni <audio> con 'src'.")
                    return Response({"error": "No se pudo extraer la URL de audio desde la página HTML de Sharpen."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                # La 'potential_audio_url' ya es la URL final y completa de S3.
                # No es necesario reconstruirla.
                parsed_extracted_url = urlparse(extracted_url)
                decoded_path = unquote(parsed_extracted_url.path)
                logger.debug(f"Path decodificado de la URL extraída: {decoded_path}")

                if "s3.amazonaws.com" in parsed_extracted_url.netloc and "/https://" in decoded_path:
                    logger.warning("Detectado patrón de URL mal formada por Sharpen (URL de Sharpen incrustada en el path de S3).")
                    parts_of_path_after_bucket = decoded_path.split('/https:/', 1) 
                    if len(parts_of_path_after_bucket) > 1:
                        corrected_host_and_path = parts_of_path_after_bucket[1].lstrip('/')
                        if not corrected_host_and_path.startswith("https://") and not corrected_host_and_path.startswith("http://"):
                                next_url_to_fetch  = "https://" + corrected_host_and_path
                        else:
                                next_url_to_fetch  = corrected_host_and_path
                        logger.info(f"URL de audio corregida: {next_url_to_fetch}")
                    else:
                        # Si no se pudo corregir el patrón, usar la URL original (seguirá fallando)
                        next_url_to_fetch = extracted_url # No se pudo corregir el patrón, usar la URL original (probablemente falle)
                        logger.warning(f"No se pudo corregir la URL mal formada en el path. Usando la URL original extraída: {next_url_to_fetch}")
                else:
                    # Si la URL no tiene el patrón de Sharpen malformado, la usamos tal cual.
                    next_url_to_fetch = extracted_url
                    logger.info(f"URL de S3 directa para el siguiente intento (sin corrección de path): {next_url_to_fetch}")
            
                current_url_to_fetch = next_url_to_fetch

            elif "application/xml" in content_type or "text/xml" in content_type:
                # Esto suele ser un error de S3 (URL expirada)
                error_content = response.text
                logger.error(f"La URL '{current_url_to_fetch}' devolvió un error XML (probablemente la URL expiró o es inválida): {error_content[:500]}")
                return Response({"error": "La URL del audio parece haber expirado o es inválida.", "details": error_content[:500]}, status=status.HTTP_400_BAD_REQUEST)
            elif "audio" in content_type or "binary/octet-stream" in content_type or "application/x-download" in content_type:
                logger.info(f"URL '{current_url_to_fetch}' devolvió directamente un archivo de audio. ¡Éxito!")
                audio_data = BytesIO(response.content)
                break # Salir del bucle, tenemos el audioo
            else:
                logger.warning(f"Content-Type inesperado para '{current_url_to_fetch}': '{content_type}'. Intentando procesar como audio de todas formas.")
                audio_data = BytesIO(response.content)
                break # Salir del bucle, asumiendo que es audio
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de red/HTTP al descargar el audio para {unique_id} desde {current_url_to_fetch}: {e}", exc_info=True)
            status_code = getattr(e.response, 'status_code', 502) if hasattr(e, 'response') else 502
            return Response({"error": f"No se pudo descargar el audio desde Sharpen: {e}"}, status=status_code)
        except Exception as e:
            logger.error(f"Error inesperado durante el proceso de análisis para {unique_id} en la URL {current_url_to_fetch}: {e}", exc_info=True)
            return Response({"error": f"Ocurrió un error al procesar la URL: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

    if not audio_data or not audio_data.getvalue():
        logger.error(f"No se pudo obtener el archivo de audio después de {max_redirects_html} intentos de extracción de HTML para {unique_id}.")
        return Response({"error": "No se pudo obtener el archivo de audio para procesamiento después de múltiples redirecciones HTML."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    logger.info(f"Tamaño de audio_data antes de transcripción: {audio_data.tell()} bytes")
    audio_data.seek(0) # Reiniciar la posición del buffer al principio
    
    logger.info(f"Iniciando transcripción para {unique_id}...")
    transcription = transcribe_audio_filelike_no_disk(audio_data, lang)
    logger.info(f"Transcripción completada para {unique_id}.")

    if isinstance(transcription_result, tuple):
        transcription_text = transcription_result[0]
        # Si tienes varios resultados en la tupla, puedes unirlos
        # transcription_text = " ".join(transcription_result)
    else:
        transcription_text = transcription_result
        
    logger.debug(f"Texto de transcripción para análisis: {transcription_text}")
    
    analysis = extract_information(transcription_text, lang=lang)
    logger.info(f"Análisis Spacy completado para {unique_id}.")

    try:
            instance = CallAnalysis.objects.create(
                audio_file=None, # O una referencia al audio de Sharpen si es aplicable
                transcript=transcription_text, # Usa la variable corregida
                high_risk_warnings=json.dumps(analysis["high_risk_warnings"]),
                call_motives=json.dumps(analysis["call_motives"]),
                motives=json.dumps(analysis.get("motivos", [])), # Campo antiguo, decide si lo mantienes
                agent_actions=json.dumps(analysis.get("acciones_agente", [])), # Campo antiguo, decide si lo mantienes
                unique_id=unique_id,
                language_used=lang,
            )
            logger.info(f"Instancia CallAnalysis creada para audio de Sharpen con ID: {instance.id}")
    except Exception as e:
        logger.error(f"Error al guardar CallAnalysis para audio de Sharpen {unique_id}: {e}", exc_info=True)
        # Decide cómo manejar este error: ¿devolver un 500 o continuar sin guardar?
        # Por ahora, simplemente logueamos y continuamos para devolver la respuesta.

    return Response({
        "status": "success",
        "transcription": transcription_text, # Usa la variable corregida
        "uniqueID": unique_id,
        "analysis": {
                    "high_risk_warnings": analysis["high_risk_warnings"],
                    "call_motives": analysis["call_motives"],
                    "motivos": analysis.get("motivos", []),
                    "agent_actions": analysis.get("acciones_agente", []),
        },    
    }, status=status.HTTP_200_OK)
