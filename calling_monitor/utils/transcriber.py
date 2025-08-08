# calling_monitor/utils/transcriber.py
import shutil # Make sure this is at the top
import wave
import json
from vosk import Model, KaldiRecognizer
import soundfile as sf
import tempfile 
import numpy as np # Needed for array manipulation if converting audio
import os # Import the os module
import io
from pydub import AudioSegment
from pydub.utils import get_prober_name, get_encoder_name, which
import mimetypes
import spacy


import logging
logger = logging.getLogger(__name__)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Define paths for both models
VOSK_MODEL_ES_PATH = os.path.join(BASE_DIR, "models", "vosk-model-small-es-0.42")
VOSK_MODEL_EN_PATH = os.path.join(BASE_DIR, "models", "vosk-model-small-en-us-0.15")

nlp = spacy.load("en_core_web_sm")


if not which("ffmpeg"):
    logger.error("❌ FFmpeg no se encontró en el PATH del sistema. Es necesario para procesar audio.")
    # Puedes lanzar una excepción o simplemente registrar el error
    # raise FileNotFoundError("FFmpeg no está instalado o no se encuentra en el PATH.")

if not which("ffprobe"):
    logger.error("❌ FFprobe no se encontró en el PATH del sistema.")

def analyze_transcript(text):
    doc = nlp(text)
    logger.debug("Tokens y POS:")
    for token in doc:
        logger.debug(f"{token.text} ({token.pos_})")
    
    logger.debug("Entidades encontradas:")
    for ent in doc.ents:
        logger.debug(f"{ent.text} - {ent.label_}")
    
    return doc

def transcribe_and_print_entities(file_like_obj, lang="en"):
    transcript, doc = transcribe_audio_filelike_no_disk(file_like_obj, lang=lang)
    print("Texto transcrito:", transcript)
    print("Entidades reconocidas:")
    for ent in doc.ents:
        print(f"  {ent.text} ({ent.label_})")
        
if __name__ == "__main__":
    # Para pruebas locales, cambiar por ruta válida
    with open("ruta/a/audio.wav", "rb") as f:
        transcribe_and_print_entities(f, lang="en")


def get_vosk_model_path(lang="es"):
    if lang == "es":
        return VOSK_MODEL_ES_PATH
    elif lang == "en":
        return VOSK_MODEL_EN_PATH
    else:
        raise ValueError("Unsupported language for Vosk model. Choose 'es' or 'en'.")

def transcribe_audio(file_path, model_path=VOSK_MODEL_ES_PATH):
    logger.debug(f"Transcribing audio from disk: {file_path} using model: {model_path}")

    model = Model(model_path)
    wf = wave.open(file_path, "rb")
    rec = KaldiRecognizer(model, wf.getframerate())

    results = []
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            res = json.loads(rec.Result())
            results.append(res.get("text", ""))
    final_result = json.loads(rec.FinalResult())
    results.append(final_result.get("text", ""))

    return " ".join(results)

def transcribe_audio_filelike(file_like_obj, model_path=VOSK_MODEL_ES_PATH): # Default to Spanish
    logger.debug(f"Transcribing file-like object using temp file, model: {model_path}")
    mime_type, _ = mimetypes.guess_type("archivo.wav")
    file_like_obj.seek(0)
    logger.debug(f"Detected MIME type: {mime_type}")

    with tempfile.NamedTemporaryFile(delete=True, suffix=".wav") as temp_wav:
        temp_wav.write(file_like_obj.read())
        temp_wav.flush()
        return transcribe_audio(temp_wav.name, model_path) # Pass model_path here

def transcribe_audio_filelike_no_disk(file_like_obj, lang="es"):
    model_path = get_vosk_model_path(lang)
    try:
        model = Model(model_path)
        file_like_obj.seek(0)

        logger.debug("Attempting to load audio with pydub...")
        audio_segment = AudioSegment.from_file(file_like_obj)

        if audio_segment.frame_rate != 16000:
            logger.debug(f"Resampling audio from {audio_segment.frame_rate}Hz to 16000Hz.")
            audio_segment = audio_segment.set_frame_rate(16000)
        
        if audio_segment.channels != 1:
            logger.debug(f"Converting audio from {audio_segment.channels} channels to mono.")
            audio_segment = audio_segment.set_channels(1)

        wav_buffer = io.BytesIO()
        audio_segment.export(wav_buffer, format="wav", parameters=["-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1"])
        wav_buffer.seek(0)

        logger.debug("Pydub successfully processed audio into WAV format in memory.")

        samplerate = audio_segment.frame_rate # Should be 16000 now
        rec = KaldiRecognizer(model, samplerate)
        logger.debug(f"KaldiRecognizer initialized with samplerate: {samplerate}.")

        results = []
        chunk_size = 4000 # Read in chunks (e.g., 4000 bytes)

        while True:
            data_chunk = wav_buffer.read(chunk_size)
            if len(data_chunk) == 0:
                break
            if rec.AcceptWaveform(data_chunk):
                part_result = json.loads(rec.Result())
                if part_result.get('text'):
                    results.append(part_result['text'])
            # else:
                # Optional: process partial results with rec.PartialResult()

        # Get the final result for any remaining audio
        final_result = json.loads(rec.FinalResult())
        if final_result.get('text'):
            results.append(final_result['text'])

        full_transcript = " ".join(results).strip()
        logger.debug(f"Full transcription result: {full_transcript}")
        # doc = analyze_transcript(full_transcript)
        return full_transcript 

    except Exception as e:
        logger.error(f"Error inside transcribe_audio_filelike_no_disk: {str(e)}", exc_info=True)
        raise