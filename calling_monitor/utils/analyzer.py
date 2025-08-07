# calling_monitor/utils/analyzer.py
import spacy
import logging
from spacy.matcher import Matcher # Importamos Matcher para detección de patrones más avanzada

logger = logging.getLogger(__name__)

# Cache de modelos Spacy
_nlp_models = {}

def get_spacy_model(lang: str):
    """
    Carga y cachea el modelo Spacy adecuado según el idioma.
    """
    if lang == "es":
        model_name = "es_core_news_sm"
    elif lang == "en":
        model_name = "en_core_web_sm"
    else:
        logger.error(f"Idioma no soportado para modelo Spacy: {lang}")
        raise ValueError(f"Idioma no soportado para modelo Spacy: {lang}. Elige 'es' o 'en'.")

    if model_name not in _nlp_models:
        logger.info(f"Cargando modelo Spacy: {model_name}...")
        try:
            nlp = spacy.load(model_name)
            _nlp_models[model_name] = nlp
            logger.info(f"Modelo Spacy {model_name} cargado y cacheado exitosamente.")
        except OSError:
            logger.error(f"Modelo Spacy {model_name} no encontrado. Intentando descargar...")
            spacy.cli.download(model_name)
            nlp = spacy.load(model_name)
            _nlp_models[model_name] = nlp
            logger.info(f"Modelo Spacy {model_name} descargado y cargado.")
    return _nlp_models[model_name]


def extract_information(transcript: str, lang: str = "es") -> dict:
    """
    Analiza la transcripción utilizando Spacy para detectar situaciones de alto riesgo
    y clasificar el motivo de la llamada.
    """
    logger.debug(f"Iniciando análisis para idioma: {lang} con longitud de transcripción: {len(transcript)}")
    nlp = get_spacy_model(lang)
    doc = nlp(transcript) # Procesar la transcripción con Spacy

    # Inicializar resultados
    high_risk_warnings = []
    call_motives = ["No clasificado"] # Por defecto, si no se detecta nada específico

    # --- Detección de Palabras Clave de Alto Riesgo ---
    # Usaremos un Matcher para patrones más robustos que simples palabras clave
    # Puedes añadir más patrones según tus necesidades.

    matcher = Matcher(nlp.vocab)

    # Patrones para Detección de Alto Riesgo (Español)
    if lang == "es":
        # Violencia/Amenazas
        matcher.add("RIESGO_VIOLENCIA", [
            [{"LEMMA": {"IN": ["amenazar", "agredir", "golpear", "matar"]}}],
            [{"LOWER": "me"}, {"LOWER": "va"}, {"LOWER": "a"}, {"LOWER": "matar"}],
            [{"LOWER": "te"}, {"LOWER": "voy"}, {"LOWER": "a"}, {"LOWER": "denunciar"}] # A veces una amenaza, dependiendo del contexto
        ])
        # Emergencias/Salud
        matcher.add("RIESGO_EMERGENCIA", [
            [{"LEMMA": {"IN": ["emergencia", "ayuda", "hospital", "ambulancia", "médico", "urgencia"]}}],
            [{"LOWER": "no"}, {"LOWER": "puedo"}, {"LOWER": "respirar"}],
            [{"LOWER": "necesito"}, {"LOWER": "ayuda"}, {"LOWER": "urgente"}]
        ])
        # Fraude/Estafa
        matcher.add("RIESGO_FRAUDE", [
            [{"LEMMA": {"IN": ["fraude", "estafa", "robo", "engañar", "extorsión"]}}],
            [{"LOWER": "me"}, {"LOWER": "robaron"}, {"LOWER": "mis"}, {"LOWER": "datos"}],
            [{"LOWER": "estafa"}, {"LOWER": "telefónica"}]
        ])
        # Suicidio/Crisis Mental
        matcher.add("RIESGO_CRISIS", [
            [{"LEMMA": {"IN": ["suicidio", "deprimido", "vida", "matarme", "ya no puedo", "cuchillo", "pistola"]}}],
            [{"LOWER": "no"}, {"LOWER": "quiero"}, {"LOWER": "vivir"}]
        ])
        # Cliente muy molesto/agresivo (podría necesitar NER para detectar insultos)
        # Esto es más complejo y quizás requiera un modelo de clasificación de sentimiento o un enfoque de reglas más sofisticado.
        # Por ahora, nos quedamos con palabras clave explícitas.
        # Ejemplo: "insultos", "groserías" -- puedes añadir palabras específicas si sabes cuáles buscar

    # Patrones para Detección de Alto Riesgo (Inglés)
    elif lang == "en":
        # Violence/Threats
        matcher.add("HIGH_RISK_VIOLENCE", [
            [{"LEMMA": {"IN": ["threaten", "assault", "hit", "kill"]}}],
            [{"LOWER": "i'm"}, {"LOWER": "going"}, {"LOWER": "to"}, {"LOWER": "kill"}, {"LOWER": "you"}],
            [{"LOWER": "i'm"}, {"LOWER": "reporting"}, {"LOWER": "you"}]
        ])
        # Emergencies/Health
        matcher.add("HIGH_RISK_EMERGENCY", [
            [{"LEMMA": {"IN": ["emergency", "help", "hospital", "ambulance", "doctor", "urgent"]}}],
            [{"LOWER": "i"}, {"LOWER": "can't"}, {"LOWER": "breathe"}],
            [{"LOWER": "i"}, {"LOWER": "need"}, {"LOWER": "urgent"}, {"LOWER": "help"}]
        ])
        # Fraud/Scam
        matcher.add("HIGH_RISK_FRAUD", [
            [{"LEMMA": {"IN": ["fraud", "scam", "theft", "deceive", "extortion"]}}],
            [{"LOWER": "my"}, {"LOWER": "data"}, {"LOWER": "was"}, {"LOWER": "stolen"}],
            [{"LOWER": "phone"}, {"LOWER": "scam"}]
        ])
        # Suicide/Mental Crisis
        matcher.add("HIGH_RISK_CRISIS", [
            [{"LEMMA": {"IN": ["suicide", "depressed", "life", "kill myself", "can't go on", "knife", "gun"]}}],
            [{"LOWER": "i"}, {"LOWER": "don't"}, {"LOWER": "want"}, {"LOWER": "to"}, {"LOWER": "live"}]
        ])

    matches = matcher(doc)
    detected_risks = set() # Usar un set para evitar duplicados

    for match_id, start, end in matches:
        span = doc[start:end]
        if nlp.vocab.strings[match_id] == "RIESGO_VIOLENCIA" or nlp.vocab.strings[match_id] == "HIGH_RISK_VIOLENCE":
            detected_risks.add(f"Advertencia: Violencia/Amenaza detectada ({span.text})")
        elif nlp.vocab.strings[match_id] == "RIESGO_EMERGENCIA" or nlp.vocab.strings[match_id] == "HIGH_RISK_EMERGENCY":
            detected_risks.add(f"Advertencia: Emergencia/Salud detectada ({span.text})")
        elif nlp.vocab.strings[match_id] == "RIESGO_FRAUDE" or nlp.vocab.strings[match_id] == "HIGH_RISK_FRAUDE":
            detected_risks.add(f"Advertencia: Fraude/Estafa detectada ({span.text})")
        elif nlp.vocab.strings[match_id] == "RIESGO_CRISIS" or nlp.vocab.strings[match_id] == "HIGH_RISK_CRISIS":
            detected_risks.add(f"Advertencia: Crisis mental/suicidio detectada ({span.text})")
        # Añade más condiciones aquí para otros tipos de riesgo

    high_risk_warnings = list(detected_risks)
    if not high_risk_warnings:
        high_risk_warnings.append("No se detectaron advertencias de alto riesgo.")

    # --- Clasificación del Motivo de la Llamada ---
    # Esto también se puede hacer con reglas o un clasificador si hay muchos motivos.
    # Usaremos LEMMA (forma base de la palabra) para ser más robustos.

    call_motives_detected = set() # Usar un set para evitar duplicados

    # Español
    if lang == "es":
        # Pedir información
        if any(lemma in [token.lemma_ for token in doc] for lemma in ["información", "saber", "consulta", "duda"]):
            call_motives_detected.add("Pedir información")
        # Agendar cita
        if any(lemma in [token.lemma_ for token in doc] for lemma in ["agendar", "cita", "programar"]):
            call_motives_detected.add("Agendar cita")
        # Cancelar cita
        if any(lemma in [token.lemma_ for token in doc] for lemma in ["cancelar", "anular", "baja"]):
            call_motives_detected.add("Cancelar cita")
        # Reagendar cita
        if any(lemma in [token.lemma_ for token in doc] for lemma in ["reagendar", "cambiar", "mover"]):
            call_motives_detected.add("Reagendar cita")
        
        # Considerar si solo quieren un motivo dominante o múltiples
        # Si 'Agendar cita' y 'Reagendar cita' están presentes, ¿cuál es más importante?
        # Para simplificar, si se detecta más de uno, los incluimos todos.

    # English
    elif lang == "en":
        # Ask for information
        if any(lemma in [token.lemma_ for token in doc] for lemma in ["information", "know", "query", "doubt"]):
            call_motives_detected.add("Ask for information")
        # Schedule appointment
        if any(lemma in [token.lemma_ for token in doc] for lemma in ["schedule", "appointment", "book"]):
            call_motives_detected.add("Schedule appointment")
        # Cancel appointment
        if any(lemma in [token.lemma_ for token in doc] for lemma in ["cancel", "annul", "revoke"]):
            call_motives_detected.add("Cancel appointment")
        # Reschedule appointment
        if any(lemma in [token.lemma_ for token in doc] for lemma in ["reschedule", "change", "move"]):
            call_motives_detected.add("Reschedule appointment")
    
    # Si se detectaron motivos específicos, reemplaza el valor por defecto
    if call_motives_detected:
        call_motives = list(call_motives_detected)

    # Las 'acciones_agente' y 'motivos' del cliente (si es que tienes esos campos separados
    # de los motivos de llamada y riesgos)
    # Por ahora, los dejo como antes, pero podrías integrarlos mejor con el análisis de Spacy
    # para un resultado más coherente.
    agent_actions = [] # Puedes rellenar esto con lógica similar a la de los motivos.

    logger.debug(f"Análisis completado. Advertencias de riesgo: {high_risk_warnings}, Motivos de llamada: {call_motives}")
    return {
        "high_risk_warnings": high_risk_warnings,
        "call_motives": call_motives,
        "motivos": ["Análisis de motivos del cliente más detallado aquí."], # Si son diferentes a call_motives
        "acciones_agente": ["Análisis de acciones del agente aquí."], # Si necesitas esto separado
    }