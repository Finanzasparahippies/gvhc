import speech_recognition as sr
from django.conf import settings
from calling_monitor.models import CallRecord

# Cargar palabras clave
keywords = settings.KEYWORDS

# Inicializa el reconocimiento de voz
recognizer = sr.Recognizer()
microphone = sr.Microphone()

def monitor_call():
    with microphone as source:
        print("Calibrando micrófono... un momento.")
        recognizer.adjust_for_ambient_noise(source, duration=3)
        print("Escuchando...")

        # Diccionario para registrar las palabras clave detectadas
        detected_keywords = {keyword: False for keyword in keywords}

        # Escucha continuamente la conversación
        while True:
            try:
                audio = recognizer.listen(source)
                # Convierte el audio a texto
                text = recognizer.recognize_google(audio)
                print(f"Agente dijo: {text}")

                # Compara el texto con las palabras clave
                for keyword in keywords:
                    if keyword.lower() in text.lower():
                        detected_keywords[keyword] = True
                        print(f"Palabra clave '{keyword}' detectada")
                         # Guarda en la base de datos
                        CallRecord.objects.create(keyword=keyword, detected=True)

                # Opcional: verifica si todas las palabras clave se han mencionado
                if all(detected_keywords.values()):
                    print("Todas las palabras clave han sido mencionadas.")
                    break  # Sal del bucle si se han mencionado todas

            except sr.UnknownValueError:
                print("No se pudo entender el audio.")
            except sr.RequestError as e:
                print(f"Error con el servicio de reconocimiento: {e}")
                break

    return detected_keywords
