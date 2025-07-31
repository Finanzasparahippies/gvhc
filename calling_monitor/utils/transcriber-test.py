import requests
import io
from pydub import AudioSegment
import speech_recognition as sr
import os

# Configura ffmpeg para pydub
FFMPEG_PATH = r'C:\Users\Agent\Documents\Zoom\config\files\gvhc\ffmpeg\bin'
os.environ["PATH"] += os.pathsep + FFMPEG_PATH
AudioSegment.converter = os.path.join(FFMPEG_PATH, "ffmpeg.exe")

url = "https://s3.amazonaws.com/iz-iz1-mixrec/con10086-30555068.wav?X-Amz-Content-Sha256=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAXN6VFYKXRT5R32NU%2F20250731%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20250731T184735Z&X-Amz-SignedHeaders=Host&X-Amz-Expires=1200&X-Amz-Signature=5b7c80f9099b1f8b5f7ea3796e27cf2aceb63b7b39a32e56071dd4275dc525a9"

response = requests.get(url)
response.raise_for_status()  # Para lanzar excepción si error HTTP

audio_bytes = io.BytesIO(response.content)

# Carga audio con pydub desde bytes
audio_segment = AudioSegment.from_file(audio_bytes)

# Convierte a mono y 16kHz para compatibilidad con speech_recognition
audio_segment = audio_segment.set_channels(1).set_frame_rate(16000)

# Exporta a WAV en memoria
wav_buffer = io.BytesIO()
audio_segment.export(wav_buffer, format="wav")
wav_buffer.seek(0)

# Transcribe usando speech_recognition
recognizer = sr.Recognizer()
with sr.AudioFile(wav_buffer) as source:
    audio_data = recognizer.record(source)

try:
    text = recognizer.recognize_google(audio_data, language='en-En')
    print("Transcripción:", text)
except sr.UnknownValueError:
    print("No se pudo entender el audio.")
except sr.RequestError as e:
    print(f"Error en el servicio de reconocimiento: {e}")
