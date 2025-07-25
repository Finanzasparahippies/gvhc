from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import openai
import os
from decouple import config
import language_tool_python


# Create your views here.
# Configuración de la API Key
openai.api_key = config('OPENAI_API_KEY')

@csrf_exempt
def grammar_correction(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_text = data.get('text')

            if user_text:
                response = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "user", "content": f"Correct the following sentence for grammar: {user_text}"}
                    ]
                )
                corrected_text = response['choices'][0]['message']['content'].strip()
                return JsonResponse({"corrected_text": corrected_text})
            else:
                return JsonResponse({"error": "No text provided"}, status=400)
        except Exception as e:
            print(f"Error en la solicitud de OpenAI: {e}")
            return JsonResponse({"error": "Internal server error"}, status=500)
    return JsonResponse({"error": "Invalid request method"}, status=405)

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


