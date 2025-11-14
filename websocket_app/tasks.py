#websocket_app/task.py
import logging
import hashlib
import json
from celery import shared_task
from .fetch_script import fetch_calls_on_hold_data, fetch_live_queue_status_data, fetch_agent_performance_data 
from users.models import User  # Importa tu modelo de usuario
from django.db import transaction
from django.utils import timezone
from django.db.models import F # Para actualizaciones atómicas y seguras
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .monitoring import get_resource_metrics
import ssl  # Asegúrate de importar ssl para usar CERT_NONE

logger = logging.getLogger(__name__)


# _last_data_checksums = {
#     'getCallsOnHoldData': None,
#     'liveQueueStatus': None,
#     # Puedes añadir más si tu full_frontend_payload crece
# }


def get_checksum(data_to_hash):
    """
    Calcula un checksum MD5 para los datos proporcionados.
    Asegura que los datos sean una lista serializable para JSON.
    """
    # Convertir a una lista si no lo es, o asegurar que sea serializable.
    # Si data_to_hash es None, lo convertimos a una lista vacía para que no falle el JSON.
    if data_to_hash is None:
        processed_data = []
    elif not isinstance(data_to_hash, list):
        processed_data = [data_to_hash] # Si es un solo elemento, lo envolvemos en una lista
    else:
        processed_data = data_to_hash # Si ya es una lista, la usamos directamente

    # Usamos sort_keys=True para asegurar un orden consistente para el hashing.
    try:
        return hashlib.md5(json.dumps(processed_data, sort_keys=True).encode('utf-8')).hexdigest()
    except TypeError as e:
        logger.error(f"TypeError al calcular checksum: {e}. Datos problemáticos: {processed_data}")
        # Retorna un checksum único para indicar un error o un estado no válido
        return "error_checksum_" + str(hash(json.dumps(processed_data, sort_keys=True))) # Intenta crear un hash único

GAMIFICATION_RULES = {
    'call_completed': 10,
    'efficient_wrap_up': 5, # Ejemplo: si wrap up es < 30s
    'new_agent_bonus': 25, # Primera vez que se procesa un agente
    'high_quality_score_bonus_per_point': 1, # 1 punto extra por cada punto de calidad
    'good_resolution_rate_threshold': 0.8, # Umbral para bono
    'good_resolution_rate_bonus': 15,
}

@shared_task
def update_agent_gamification_scores():
    logger.info("Iniciando tarea de actualización de gamificación de agentes...")
    try:
        sharpen_agent_data = async_to_sync(fetch_agent_performance_data)()
        
        # Corregir la indentación de esta sección
        if not sharpen_agent_data:
            logger.warning("No se recibieron datos de agentes de Sharpen. Saltando actualización de gamificación.")
            return # Usa 'return' para salir de la función, 'continue' solo funciona en bucles

        for agent_data in sharpen_agent_data:
            sharpen_username = agent_data.get('username')
            if not sharpen_username:
                logger.warning(f"Dato de agente de Sharpen sin 'username'. Saltando: {agent_data}")
                continue

            try:
                with transaction.atomic():
                    user, created = User.objects.get_or_create(
                        sharpen_username=sharpen_username,
                        defaults={
                            'username': sharpen_username,
                            'email': f'{sharpen_username.replace(".", "")}@example.com',
                            'first_name': sharpen_username.split('.')[0].capitalize() if '.' in sharpen_username else '',
                            'last_name': sharpen_username.split('.')[1].capitalize() if '.' in sharpen_username else '',
                            'role': 'agent',
                        }
                    )

                    user = User.objects.select_for_update().get(pk=user.pk)

                    points_for_this_agent_round = 0
                    
                    current_calls_handled = agent_data.get('calls_handled_today', 0)
                    current_quality_score = agent_data.get('quality_score', 0.0)
                    current_resolution_rate = agent_data.get('issue_resolution_rate', 0.0)

                    # --- Lógica de Puntos Incremental ---
                    if created:
                        points_for_this_agent_round += GAMIFICATION_RULES['new_agent_bonus']
                        logger.info(f"Agente {sharpen_username}: +{GAMIFICATION_RULES['new_agent_bonus']} por bono de nuevo agente.")

                    new_calls = current_calls_handled - user.last_calls_handled
                    if new_calls > 0:
                        points_for_this_agent_round += new_calls * GAMIFICATION_RULES['call_completed']
                        logger.debug(f"Agente {sharpen_username}: +{new_calls * GAMIFICATION_RULES['call_completed']} por {new_calls} nuevas llamadas.")

                    # Use F() expressions for safe updates of points
                    if points_for_this_agent_round > 0:
                        user.gamification_points = F('gamification_points') + points_for_this_agent_round
                        user.last_point_update = timezone.now()
                        logger.info(f"Agregados {points_for_this_agent_round} puntos a {user.username}. Total: {user.gamification_points}. Nivel: {user.gamification_level}")

                    # Update all last known values
                    user.last_calls_handled = current_calls_handled
                    user.last_quality_score = current_quality_score
                    user.last_resolution_rate = current_resolution_rate
                    
                    # Save all changes in a single query within the transaction
                    user.save(update_fields=['gamification_points', 'last_calls_handled', 
                                             'last_quality_score', 'last_resolution_rate', 'last_point_update'])
            
            except User.DoesNotExist:
                logger.warning(f"Usuario Django no encontrado para Sharpen username: {sharpen_username}. Saltando.")
            except Exception as e:
                logger.error(f"Error procesando datos para Sharpen username {sharpen_username}: {e}", exc_info=True)

    except Exception as e:
        logger.exception(f"Error general en update_agent_gamification_scores: {e}")


@shared_task
def broadcast_calls_update():
    try:
        # 1. Leer el último estado desde la caché
        from django.core.cache import cache
        last_on_hold_checksum = cache.get('last_on_hold_checksum')
        last_live_queue_checksum = cache.get('last_live_queue_checksum')
        
        logger.debug(f"Last checksums from cache: OnHold={last_on_hold_checksum}, LiveQueue={last_live_queue_checksum}")

        channel_layer = get_channel_layer()
        if not channel_layer:
            logging.error("Error: Channel layer not configured.")
            return

        payload_on_hold = async_to_sync(fetch_calls_on_hold_data)()
        calls_on_hold_data = payload_on_hold.get('getCallsOnHoldData', []) if isinstance(payload_on_hold, dict) else []

        payload_live_queue = async_to_sync(fetch_live_queue_status_data)()
        live_queue_status_data = payload_live_queue.get('liveQueueStatus', []) if isinstance(payload_live_queue, dict) else []

        new_on_hold_checksum = get_checksum(calls_on_hold_data)
        new_live_queue_checksum = get_checksum(live_queue_status_data)

        logger.debug(f"New checksums: OnHold={new_on_hold_checksum}, LiveQueue={new_live_queue_checksum}")
        transitioned_to_empty = (
            (calls_on_hold_data == [] and last_on_hold_checksum not in [None, get_checksum([])]) or
            (live_queue_status_data == [] and last_live_queue_checksum not in [None, get_checksum([])])
        )
        # 2. Comparar los nuevos checksums con los de la caché
        if (
            new_on_hold_checksum != last_on_hold_checksum
            or new_live_queue_checksum != last_live_queue_checksum
            or transitioned_to_empty
        ):
            logger.info("[Celery] Cambios detectados. Emitiendo actualización a clientes WebSocket.")

            full_frontend_payload = {
                "type": "dataUpdate",
                "payload": {
                "getCallsOnHoldData": calls_on_hold_data,
                "getLiveQueueStatusData": live_queue_status_data
                }
            }

            message_to_send = json.dumps(full_frontend_payload)

            async_to_sync(channel_layer.group_send)(
                "calls",
                {
                    "type": "send.message", 
                    "payload": message_to_send 
                }
            )
        # 3. Guardar el nuevo estado en la caché
            cache.set('last_on_hold_checksum', new_on_hold_checksum)
            cache.set('last_live_queue_checksum', new_live_queue_checksum)

        else:
            logger.info("[Celery] No se detectaron cambios en los datos. No se envía actualización a los clientes.")
    except Exception as e:
        logger.exception(f"Error en Celery broadcast_calls_update: {e}")



@shared_task
def log_system_metrics():
    try:
        metrics = get_resource_metrics()
        logger.info(f"[Metrics] RAM: {metrics['memory_used_mb']:.2f} MB ({metrics['memory_percent']:.2f}%), CPU: {metrics['cpu_percent']:.2f}%")
    except Exception as e:
        logger.exception("Error en Celery log_system_metrics:")