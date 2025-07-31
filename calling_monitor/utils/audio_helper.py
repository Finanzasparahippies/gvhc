# utils/audio_helpers.py (o donde prefieras)
import requests
import io
import logging

logger = logging.getLogger(__name__)

def download_audio_as_filelike(audio_url: str) -> io.BytesIO:
    """
    Descarga un archivo de audio desde una URL y lo devuelve como un objeto BytesIO.
    """
    logger.info(f"Descargando audio desde URL: {audio_url}")
    try:
        response = requests.get(audio_url, stream=True, timeout=30)
        response.raise_for_status()

        content_type = response.headers.get('Content-Type', '').lower()
        logger.debug(f"Content-Type recibido: {content_type}")

        if not ('audio' in content_type or 'binary/octet-stream' in content_type):
            # Intenta decodificar el cuerpo de la respuesta para un log más útil
            error_body = response.content.decode('utf-8', errors='ignore')
            logger.error(f"La URL devolvió un Content-Type inesperado: '{content_type}'. El contenido es: {error_body[:500]}")
            raise ValueError(f"La URL no devolvió datos de audio. Content-Type: {content_type}")
        
        audio_bytes = io.BytesIO(response.content)
        audio_bytes.seek(0)
        logger.info("Audio descargado correctamente como BytesIO")
        return audio_bytes
    
    except requests.RequestException as e:
        logger.error(f"Error de red al descargar audio desde la URL: {e}", exc_info=True)
        raise # Vuelve a lanzar la excepción para que la vista la maneje

    except ValueError as e:
        logger.error(f"Error de validación de contenido: {e}", exc_info=True)
        raise # Vuelve a lanzar la excepción para que la vista la maneje