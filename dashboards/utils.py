import pytz
import re
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

HERMOSILLO_TZ = pytz.timezone('America/Hermosillo')
UTC_TZ = pytz.utc

def convert_query_times_to_utc(query: str) -> str:
    """
    Busca fechas en formato 'YYYY-MM-DD HH:MM:SS' en una consulta SQL,
    asume que están en hora de Hermosillo, las convierte a UTC y las reemplaza.
    Utiliza dos patrones regex para mayor robustez.
    """
    datetime_pattern = re.compile(r"""
        (['"])                                  # Comilla de apertura (grupo 1)
        (\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}(?::\d{2})?)   # Fecha/hora con T o espacio (grupo 2)
        \1                                      # Comilla de cierre (referencia a grupo 1)
    """, re.IGNORECASE | re.VERBOSE)

    def convert_to_utc_string(local_time_str: str) -> str:
        """Función auxiliar para convertir un string de fecha local a UTC."""
        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M"
        ]
        dt_local = None
        for fmt in formats:
            try:
                dt_local = datetime.strptime(local_time_str, fmt)
                break
            except ValueError:
                continue
        if dt_local is None:
            logger.warning(f"No se pudo parsear la fecha/hora para conversión a UTC: '{local_time_str}'. Se dejará sin modificar.")
            return local_time_str # Devuelve el string original

        dt_localized = HERMOSILLO_TZ.localize(dt_local)
        dt_utc = dt_localized.astimezone(UTC_TZ)
        utc_time_str = dt_utc.strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"Conversión de fecha: '{local_time_str}' (Hermosillo) -> '{utc_time_str}' (UTC)")
        return utc_time_str

    def replacer(match):
        quote_char = match.group(1) # Captura si es comilla simple o doble
        local_time_str = match.group(2)

        converted_time_str = convert_to_utc_string(local_time_str)
        # Reconstruye el string con el mismo tipo de comilla que se encontró
        return f"{quote_char}{converted_time_str}{quote_char}"

    # Aplica la conversión usando el nuevo patrón y la función replacer
    # Usamos sub para reemplazar todas las ocurrencias
    final_query = datetime_pattern.sub(replacer, query)

    return final_query

# You might also want to move convert_result_datetimes_to_local here if it's also a general utility.
# For now, let's assume it might have dependencies that tie it more to views.
def convert_result_datetimes_to_local(result: dict) -> dict:
    """
    Convierte los campos de fecha/hora en la respuesta 'result' de UTC a hora local (Hermosillo).
    """
    potential_time_field_names  = [
                'startTime', 'StartTime', 'answerTime', 'AnswerTime', 'endTime', 'EndTime', 'created_at', 'updated_at', 'timestamp', 'intervals',
                'lastLogin', 'lastLogout', 'currentStatusDuration', 'lastCallTime', 'lastPauseTime', 'pauseTime', 'PauseTime', 'loginTime', 'LoginTime',
                'logoutTime', 'LogoutTime', 'lastStatusChange'
    ]
    data_to_process = None
    is_table_string = False
    is_single_object = False # Nueva bandera para saber si es un objeto único


    if 'data' in result and isinstance(result['data'], list):
        data_to_process = result['data']
        logger.debug("Procesando fechas en la clave 'data' (lista).")
    elif 'getAgentsData' in result and isinstance(result['getAgentsData'], list):
        data_to_process = result['getAgentsData']
        logger.debug("Procesando fechas en la clave 'getAgentsData' (lista de agentes).")

    elif 'table' in result and isinstance(result['table'], str):

        try:
            table_data = json.loads(result['table'])
            if isinstance(table_data, list):
                data_to_process = table_data
                is_table_string = True # Marcamos que viene de un string 'table'
                logger.debug("Procesando fechas en la clave 'table' (parsed JSON string).")
            else:
                data_to_process = [table_data]
                is_table_string = True
                is_single_object = True
                logger.debug("Procesando fechas en la clave 'table' (parsed JSON string, objeto único).")
        except json.JSONDecodeError as e:
            logger.error(f"Error al parsear el JSON de la clave 'table': {e}. El contenido era: {result.get('table')}")
    elif 'getAgentStatusData' in result and isinstance(result['getAgentStatusData'], dict):
            data_to_process = [result['getAgentStatusData']] # Envuelve el objeto en una lista para procesarlo
            is_single_object = True # Marca que es un objeto único
            logger.debug("Procesando fechas en la clave 'getAgentStatusData' (objeto único).")
    elif isinstance(result, dict): # Si el resultado completo es un dict y no tiene las claves anteriores
            # Esto podría ser para respuestas donde la data viene directamente en el root del JSON
            # (aunque menos común para APIs que devuelven data tabulada)
            # Aquí, podrías decidir si quieres procesar el diccionario completo
            # Por ahora, nos enfocamos en las claves conocidas.
            pass
    
    if data_to_process is None:
        logger.info("No se encontraron datos procesables ('data' o 'table' como lista) para la conversión de fechas. Devolviendo resultado original.")
        return result

    # Ahora procesa los datos
    processed_data = []
    for row in data_to_process:
        if not isinstance(row, dict):
            logger.warning(f"Se encontró una fila no-diccionario en los datos procesables: {row}. Saltando.")
            processed_data.append(row) # Incluye la fila original si no es un diccionario
            continue
        modified_row = row.copy() 

        for key, value in modified_row.items():
            # Normaliza la clave para la comparación para ser más flexible
            normalized_key_for_comparison = key.lower().replace(' ', '')
            
            # Comprueba si el nombre del campo está en nuestra lista de nombres de campos de tiempo
            # O si el nombre normalizado sugiere que es un campo de tiempo
            is_potential_time_field = key in potential_time_field_names or \
                any(name.lower().replace(' ', '') == normalized_key_for_comparison for name in potential_time_field_names)

            if is_potential_time_field and isinstance(value, str) and value:
                try:
                    # Intenta parsear con el formato común "YYYY-MM-DD HH:MM:SS"
                    dt_utc = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                    dt_utc_localized = UTC_TZ.localize(dt_utc)
                    dt_local = dt_utc_localized.astimezone(HERMOSILLO_TZ)
                    modified_row[key] = dt_local.strftime("%Y-%m-%d %H:%M:%S")
                    # logger.info(f"Conversión de fecha para campo '{key}': '{value}' (UTC) -> '{row[key]}' (Hermosillo)")
                except ValueError:
                    logger.warning(f"Formato de fecha inesperado para campo '{key}', valor '{value}'. Intentando otros formatos...")
                    # Podrías añadir más intentos de parseo aquí si esperas otros formatos
                    # Por ejemplo, si los segundos son opcionales o si hay milisegundos.
                    try: # Intento para el formato ISO si es que Sharpen lo usa en algún campo
                        dt_utc = datetime.fromisoformat(value.replace('Z', '+00:00')) # Manejar 'Z' para UTC
                        dt_utc_localized = UTC_TZ.localize(dt_utc) if dt_utc.tzinfo is None else dt_utc
                        dt_local = dt_utc_localized.astimezone(HERMOSILLO_TZ)
                        modified_row[key] = dt_local.strftime("%Y-%m-%d %H:%M:%S")
                        logger.debug(f"Conversión ISO para campo '{key}': '{value}' (UTC) -> '{row[key]}' (Hermosillo)")
                    except ValueError:
                        logger.warning(f"No se pudo parsear la fecha '{value}' con formatos conocidos para campo '{key}'. Dejando original.")
                    except Exception as e:
                        logger.error(f"Error inesperado durante la conversión de fecha para campo '{key}', valor '{value}'. Error: {e}")
        processed_data.append(modified_row) # Agrega la fila procesada

    
    # Si los datos originales vinieron de un string 'table', vuelve a serializar
    if is_table_string:
        if is_single_object:
            result['table'] = json.dumps(processed_data[0])
            logger.info("Fechas convertidas a zona horaria local y re-serializadas en 'table'.")
        else: # Si vinieron de 'data'
            result['table'] = json.dumps(processed_data)
            logger.info("Fechas convertidas a zona horaria local en 'data'.")
            
    elif 'data' in result and isinstance(result['data'], list):
        result['data'] = processed_data
        logger.info("Fechas convertidas a zona horaria local en 'data'.")
    elif 'getAgentsData' in result and isinstance(result['getAgentsData'], list):
        result['getAgentsData'] = processed_data
        logger.info("Fechas convertidas a zona horaria local en 'getAgentsData'.")
    elif 'getAgentStatusData' in result and isinstance(result['getAgentStatusData'], dict):
        result['getAgentStatusData'] = processed_data[0] # Desenvuelve el objeto de la lista
        logger.info("Fechas convertidas a zona horaria local en 'getAgentStatusData'.")
    return result