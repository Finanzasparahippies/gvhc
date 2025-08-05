# calling_monitor/utils/transcriber.py
import wave
import json
from vosk import Model, KaldiRecognizer
import soundfile as sf
import tempfile 
import numpy as np # Needed for array manipulation if converting audio
import os # Import the os module
import io
from pydub import AudioSegment
from pydub.utils import get_prober_name, get_encoder_name
import shutil # Make sure this is at the top
import mimetypes



import logging
logger = logging.getLogger(__name__)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Define paths for both models
VOSK_MODEL_ES_PATH = os.path.join(BASE_DIR, "models", "vosk-model-small-es-0.42")
VOSK_MODEL_EN_PATH = os.path.join(BASE_DIR, "models", "vosk-model-small-en-us-0.15")

# FFMPEG_PATH = r'C:\Users\Agent\Documents\Zoom\config\files\gvhc\ffmpeg\bin' # O C:\ffmpeg\bin, etc.
# AudioSegment.converter = os.path.join(FFMPEG_PATH, 'ffmpeg.exe') # Para Windows

# # FFMPEG_BIN_DIR = os.path.join(BASE_DIR, "ffmpeg", "bin")
# os.environ["PATH"] += os.pathsep + FFMPEG_PATH

# logger.debug(f"FFMPEG_BIN_DIR: {FFMPEG_PATH}")

ffmpeg_path = shutil.which("ffmpeg")
ffprobe_path = shutil.which("ffprobe")

if ffmpeg_path:
    logger.debug(f"ffmpeg found at: {ffmpeg_path}")
    AudioSegment.converter = ffmpeg_path
else:
    logger.error(f"ffmpeg NOT found in PATH. Current PATH: {os.environ.get('PATH')}")
    raise FileNotFoundError("ffmpeg executable not found in system PATH. Please install FFmpeg and add it to your system's PATH.")

if ffprobe_path:
    logger.debug(f"ffprobe found at: {ffprobe_path}")
    AudioSegment.probe = ffprobe_path # pydub uses .probe for ffprobe, not .prober_name
else:
    logger.error(f"ffprobe NOT found in PATH. Current PATH: {os.environ.get('PATH')}")
    raise FileNotFoundError("ffprobe executable not found in system PATH. Please install FFmpeg and add it to your system's PATH.")

# --- END NEW VERIFICATION STEP ---
# try:
#     # Set the full path to the executables
#     get_prober_name._path = os.path.join(FFMPEG_PATH, "ffprobe.exe")
#     get_encoder_name._path = os.path.join(FFMPEG_PATH, "ffmpeg.exe")
#     logger.debug(f"Pydub's internal ffmpeg path set to: {get_encoder_name._path}")
#     logger.debug(f"Pydub's internal ffprobe path set to: {get_prober_name._path}")
# except AttributeError:
#     # Handle cases where _path might not be directly settable in some pydub versions
#     logger.warning("Could not set pydub's internal ffmpeg/ffprobe paths directly via _path attribute. Relying on PATH environment variable.")
#     pass # Continue, relying on the os.environ["PATH"] modificatio-


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
    logger.debug(f"Starting transcribe_audio_filelike_no_disk for model: {model_path} (Language: {lang})")
    
    if hasattr(file_like_obj, 'seek'):
        # Si es un objeto file-like, intenta volver al principio
        logger.debug(f"Audio file-like object size (approx): {len(file_like_obj.read())} bytes")
        file_like_obj.seek(0) # Vuelve al principio para que pydub lo lea de nuevo

        if not ffmpeg_path: # This check relies on the global ffmpeg_path variable
            raise FileNotFoundError("FFmpeg executable not found. Cannot process audio.")
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
        return full_transcript

    except Exception as e:
        logger.error(f"Error inside transcribe_audio_filelike_no_disk: {str(e)}", exc_info=True)
        raise