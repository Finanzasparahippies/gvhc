# calling_monitor/utils/analyzer.py
# import spacy
import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
# nlp = spacy.load("es_core_news_sm")

def extract_information(transcript):
    tokens = word_tokenize(transcript.lower())
    motives = []
    if "cancelar" in tokens:
        motives.append("Cancelar cita")
    if "agendar" in tokens or "programar" in tokens:
        motives.append("Agendar cita")
    if "cambiar" in tokens:
        motives.append("Reprogramar cita")

    # Extrae fechas y nombres con reglas heurísticas o librerías adicionales, o usa spaCy si quieres
    # Aquí puedes agregar reglas propias o usar otras librerías NER como flair o transformers

    agent_actions = []
    if re.search(r"(su cita ha sido.*(cancelada|programada))", transcript, re.I):
        agent_actions.append("Confirmación de acción")
    if "no se pudo" in transcript:
        agent_actions.append("Problema sin resolver")

    return {
        "motivos": motives or ["Desconocido"],
        "nombres_detectados": [],  # aquí puedes añadir heurística propia si quieres
        "fechas_detectadas": [],
        "acciones_agente": agent_actions or ["No claras"]
    }
