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

import logging
logger = logging.getLogger(__name__)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Define paths for both models
VOSK_MODEL_ES_PATH = os.path.join(BASE_DIR, "models", "vosk-model-small-es-0.42")
VOSK_MODEL_EN_PATH = os.path.join(BASE_DIR, "models", "vosk-model-small-en-us-0.15")

FFMPEG_BIN_DIR = r"C:\Users\Agent\Documents\Zoom\config\files\gvhc\ffmpeg"
# FFMPEG_BIN_DIR = os.path.join(BASE_DIR, "ffmpeg", "bin")
os.environ["PATH"] += os.pathsep + FFMPEG_BIN_DIR

logger.debug(f"FFMPEG_BIN_DIR: {FFMPEG_BIN_DIR}")

ffmpeg_path = shutil.which("ffmpeg")
ffprobe_path = shutil.which("ffprobe")

if ffmpeg_path:
    logger.debug(f"ffmpeg found at: {ffmpeg_path}")
else:
    logger.error(f"ffmpeg NOT found in PATH. Current PATH: {os.environ.get('PATH')}")

if ffprobe_path:
    logger.debug(f"ffprobe found at: {ffprobe_path}")
else:
    logger.error(f"ffprobe NOT found in PATH. Current PATH: {os.environ.get('PATH')}")
# --- END NEW VERIFICATION STEP ---
try:
    # Set the full path to the executables
    get_prober_name._path = os.path.join(FFMPEG_BIN_DIR, "ffprobe.exe")
    get_encoder_name._path = os.path.join(FFMPEG_BIN_DIR, "ffmpeg.exe")
    logger.debug(f"Pydub's internal ffmpeg path set to: {get_encoder_name._path}")
    logger.debug(f"Pydub's internal ffprobe path set to: {get_prober_name._path}")
except AttributeError:
    # Handle cases where _path might not be directly settable in some pydub versions
    logger.warning("Could not set pydub's internal ffmpeg/ffprobe paths directly via _path attribute. Relying on PATH environment variable.")
    pass # Continue, relying on the os.environ["PATH"] modificatio-


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
    with tempfile.NamedTemporaryFile(delete=True, suffix=".wav") as temp_wav:
        temp_wav.write(file_like_obj.read())
        temp_wav.flush()
        return transcribe_audio(temp_wav.name, model_path) # Pass model_path here

def transcribe_audio_filelike_no_disk(file_like_obj, lang="es"):
    model_path = get_vosk_model_path(lang)
    logger.debug(f"Starting transcribe_audio_filelike_no_disk for model: {model_path} (Language: {lang})")
    
    try:
        if not ffmpeg_path: # This check relies on the global ffmpeg_path variable
            raise FileNotFoundError("FFmpeg executable not found. Cannot process audio.")
        model = Model(model_path)
        file_like_obj.seek(0)

        logger.debug("Attempting to load audio with pydub...")
        try:


 
            audio_segment = AudioSegment.from_file(file_like_obj)
        except Exception as pydub_err:
            logger.error(f"Pydub failed to load audio. Make sure ffmpeg is correctly installed and accessible. Error: {pydub_err}", exc_info=True)
            raise # Re-raise if pydub can't handle it at all.

        if audio_segment.frame_rate != 16000:
            logger.debug(f"Resampling audio from {audio_segment.frame_rate}Hz to 16000Hz.")
            audio_segment = audio_segment.set_frame_rate(16000)
        
        if audio_segment.channels != 1:
            logger.debug(f"Converting audio from {audio_segment.channels} channels to mono.")
            audio_segment = audio_segment.set_channels(1)

        wav_buffer = io.BytesIO()
        audio_segment.export(wav_buffer, format="wav")
        wav_buffer.seek(0)

        logger.debug("Pydub successfully processed audio into WAV format in memory.")

        data, samplerate = sf.read(wav_buffer)
        logger.debug(f"Soundfile read: data shape={data.shape}, samplerate={samplerate}")

        if data.dtype != 'int16':
            data = (data * 32767).astype('int16')
            logger.debug(f"Converted audio data to int16. New dtype: {data.dtype}")

        rec = KaldiRecognizer(model, samplerate)
        logger.debug("KaldiRecognizer initialized.")

        audio_bytes_for_vosk = data.tobytes()
        
        chunk_size = 4000 
        results = []
        
        for i in range(0, len(audio_bytes_for_vosk), chunk_size * data.itemsize):
            chunk = audio_bytes_for_vosk[i : i + chunk_size * data.itemsize]
            if rec.AcceptWaveform(chunk):
                res = json.loads(rec.Result())
                results.append(res.get("text", ""))
        
        final_result = json.loads(rec.FinalResult())
        results.append(final_result.get("text", ""))
        
        transcription = " ".join(results)
        logger.debug(f"Full transcription result: {transcription}")
        return transcription

    except Exception as e:
        logger.error(f"Error inside transcribe_audio_filelike_no_disk: {str(e)}", exc_info=True)
        raise