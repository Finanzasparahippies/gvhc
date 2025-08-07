# utils/audio_helpers.py (o donde prefieras)
import requests
from io import BytesIO
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote, urlparse

logger = logging.getLogger(__name__)

def get_audio_from_url(audio_url: str) -> BytesIO:
    """
    Descarga el audio desde una URL, manejando redirecciones a través de HTML.
    Devuelve un objeto BytesIO con el contenido del audio.
    """
    current_url = audio_url
    max_redirects_html = 3

    for i in range(max_redirects_html):
        try:
            logger.info(f"Intentando obtener contenido de: {current_url} (Intento {i+1})")
            response = requests.get(current_url, timeout=60, allow_redirects=True)
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "").lower()

            if "text/html" in content_type:
                logger.info("URL devolvió HTML. Buscando la URL de audio real.")
                soup = BeautifulSoup(response.text, "html.parser")
                source_tag = soup.find("source")
                audio_tag = soup.find("audio")
                extracted_url = None

                if source_tag and source_tag.has_attr("src"):
                    extracted_url = source_tag["src"]
                elif audio_tag and audio_tag.has_attr("src"):
                    extracted_url = audio_tag["src"]
                
                if extracted_url:
                    # Lógica para corregir la URL malformada de Sharpen
                    parsed_extracted_url = urlparse(extracted_url)
                    decoded_path = unquote(parsed_extracted_url.path)

                    if "s3.amazonaws.com" in parsed_extracted_url.netloc and "/https://" in decoded_path:
                        parts = decoded_path.split('/https:/', 1) 
                        if len(parts) > 1:
                            corrected_host_and_path = parts[1].lstrip('/')
                            current_url = "https://" + corrected_host_and_path if not corrected_host_and_path.startswith("http") else corrected_host_and_path
                        else:
                            raise ValueError("No se pudo corregir la URL mal formada.")
                    else:
                        current_url = extracted_url
                else:
                    raise ValueError("No se pudo encontrar una URL de audio en el HTML.")

            elif "audio" in content_type or "binary/octet-stream" in content_type or "application/x-download" in content_type:
                logger.info("URL devolvió directamente un archivo de audio. ¡Éxito!")
                return BytesIO(response.content)
            else:
                logger.warning(f"Content-Type inesperado: '{content_type}'. Intentando procesar como audio.")
                return BytesIO(response.content)

        except requests.exceptions.RequestException as e:
            logger.error(f"Error de red/HTTP al descargar audio desde {current_url}: {e}")
            raise
        except ValueError as e:
            logger.error(f"Error de procesamiento de URL: {e}")
            raise

    raise TimeoutError("No se pudo obtener el archivo de audio después de múltiples redirecciones HTML.")