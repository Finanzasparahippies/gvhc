#websocket_app/task.py
import logging
import hashlib
import json
from celery import shared_task
from .fetch_script import fetch_calls_on_hold_data, fetch_live_queue_status_data
from users.models import User  # Importa tu modelo de usuario
from django.db import transaction
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .fetch_script import fetch_calls_on_hold_data
from .monitoring import get_resource_metrics

logger = logging.getLogger(__name__)

_last_data_checksums = {
    'getCallsOnHoldData': None,
    'liveQueueStatus': None,
    # Puedes añadir más si tu full_frontend_payload crece
}


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

        for agent_data in sharpen_agent_data:
            sharpen_username = agent_data.get('username') # Clave 'username' del resultado de Sharpen
            
            # Si Sharpen retorna directamente un Call I D reciente o un contador de llamadas
            # que puedes usar para detectar nuevas llamadas procesadas desde la última vez.
            # Por ahora, nos basaremos en los datos totales que trae `fetch_agent_performance_data`
            # y recalcularemos los puntos cada vez, lo cual es más simple inicialmente.

            if not sharpen_username:
                logger.warning(f"Dato de agente de Sharpen sin 'username'. Saltando: {agent_data}")
                continue

            try:
                # Usar select_for_update() para evitar condiciones de carrera al actualizar puntos
                with transaction.atomic():
                    user = User.objects.select_for_update().get(sharpen_username=sharpen_username)

                    # Calcula los puntos para esta ronda de actualización.
                    # Aquí es donde decides cómo tus métricas de Sharpen se traducen en puntos.
                    
                    # Para evitar sumar puntos repetidamente por las mismas métricas
                    # (ej. 10 puntos por 'calls_handled_today' cada vez que corre la tarea),
                    # necesitas una forma de saber si ya los has contado.
                    # La forma más robusta es que Sharpen te dé métricas "incrementales" o
                    # que tú guardes el estado anterior de la métrica en tu modelo User.

                    # Para un inicio simple, puedes otorgar puntos basándote en un **cambio**
                    # en las métricas desde la última vez, o puntos por el total *acumulado*
                    # si las métricas de Sharpen se resetean diariamente.

                    # VAMOS A USAR UN ENFOQUE BASADO EN CAMBIOS PARA UN EJEMPLO MÁS ROBUSTO:
                    # Añade estos campos a tu modelo User si no los tienes:
                    # last_calls_handled_today = models.IntegerField(default=0)
                    # last_quality_score = models.IntegerField(default=0) # O FloatField

                    points_for_this_agent_round = 0
                    current_calls_handled = agent_data.get('calls_handled_today', 0)
                    current_quality_score = agent_data.get('quality_score', 0)
                    current_resolution_rate = agent_data.get('issue_resolution_rate', 0)

                    # Puntos por llamadas nuevas manejadas (si las métricas de Sharpen son diarias/incrementales)
                    # Si Sharpen te da el TOTAL de llamadas manejadas HOY, y quieres puntos por llamadas *nuevas* desde la última ejecución:
                    # (Esto requiere que guardes el 'calls_handled_today' de Sharpen del AGENTE la última vez)
                    
                    # Asumiendo que `agent_data['calls_handled_today']` es el *total* para hoy:
                    # Una forma de manejar esto es dar puntos basados en la diferencia con el total acumulado
                    # en tu modelo `User.total_calls_handled`
                    
                    # Opción 1: Sumar puntos basados en la diferencia de llamadas manejadas desde la última vez
                    new_calls = current_calls_handled - user.total_calls_handled
                    if new_calls > 0:
                        points_for_this_agent_round += new_calls * GAMIFICATION_RULES['call_completed']
                        logger.debug(f"Agente {sharpen_username}: +{new_calls * GAMIFICATION_RULES['call_completed']} por {new_calls} nuevas llamadas.")
                        user.total_calls_handled = current_calls_handled # Actualiza el total en tu modelo
                        
                    # Opción 2: Bono por calidad (ejemplo)
                    # Si el quality_score es la media acumulada, podríamos dar puntos si sube
                    # O si excede un umbral. Aquí, un bono simple por superar cierto score.
                    if current_quality_score >= 90 and user.last_quality_score < 90: # Solo una vez que cruza el umbral
                         points_for_this_agent_round += (current_quality_score - user.last_quality_score) * GAMIFICATION_RULES['high_quality_score_bonus_per_point'] # Da puntos por cada punto de calidad superior
                         logger.debug(f"Agente {sharpen_username}: +{ (current_quality_score - user.last_quality_score) * GAMIFICATION_RULES['high_quality_score_bonus_per_point']} por mejora/mantenimiento de calidad.")
                         user.last_quality_score = current_quality_score
                    
                    # Opción 3: Bono por tasa de resolución
                    if current_resolution_rate >= GAMIFICATION_RULES['good_resolution_rate_threshold'] and user.last_resolution_rate < GAMIFICATION_RULES['good_resolution_rate_threshold']:
                        points_for_this_agent_round += GAMIFICATION_RULES['good_resolution_rate_bonus']
                        logger.debug(f"Agente {sharpen_username}: +{GAMIFICATION_RULES['good_resolution_rate_bonus']} por alta tasa de resolución.")
                        user.last_resolution_rate = current_resolution_rate # Asegúrate de tener este campo en tu User model


                    # Si es la primera vez que procesamos este agente y ya tiene datos, dale un bono de inicio
                    # Esto requiere un flag `is_new_agent_processed` en tu User model
                    # if not user.first_processed_gamification_data:
                    #     points_for_this_agent_round += GAMIFICATION_RULES['new_agent_bonus']
                    #     user.first_processed_gamification_data = True
                    #     logger.debug(f"Agente {sharpen_username}: +{GAMIFICATION_RULES['new_agent_bonus']} por bono de nuevo agente.")


                    if points_for_this_agent_round > 0:
                        user.add_points(points_for_this_agent_round)
                        user.last_point_update = timezone.now() # Actualiza la última vez que se actualizaron los puntos
                        user.save(update_fields=['total_calls_handled', 'last_point_update', 'last_quality_score', 'last_resolution_rate']) # Asegúrate de guardar los campos actualizados
                        logger.info(f"Agregados {points_for_this_agent_round} puntos a {user.username}. Total: {user.gamification_points}. Nivel: {user.gamification_level}")
                    else:
                        logger.debug(f"No hay puntos que añadir para {user.username} en esta ronda.")

            except User.DoesNotExist:
                logger.warning(f"Usuario Django no encontrado para Sharpen username: {sharpen_username}. Saltando.")
            except Exception as e:
                logger.error(f"Error procesando datos para Sharpen username {sharpen_username}: {e}", exc_info=True) # exc_info=True para traceback completo

    except Exception as e:
        logger.exception(f"Error general en update_agent_gamification_scores: {e}")


@shared_task
def broadcast_calls_update():
    global _last_data_checksums # Importante: indica que vas a modificar esta variable global
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            logging.error("Error: Channel layer not configured.")
            return
        
        payload_on_hold = async_to_sync(fetch_calls_on_hold_data)()
        calls_on_hold_data = payload_on_hold.get('getCallsOnHoldData', []) if isinstance(payload_on_hold, dict) else []
        current_calls_on_hold_checksum = get_checksum(calls_on_hold_data)

        payload_live_queue = async_to_sync(fetch_live_queue_status_data)()
        live_queue_status_data = payload_live_queue.get('liveQueueStatus', []) if isinstance(payload_live_queue, dict) else []
        current_live_queue_status_checksum = get_checksum(live_queue_status_data)

        full_frontend_payload = {
            "getCallsOnHoldData": calls_on_hold_data,
            "getLiveQueueStatusData": live_queue_status_data
        }
        data_changed = False

        if current_calls_on_hold_checksum != _last_data_checksums['getCallsOnHoldData']:
            data_changed = True
            _last_data_checksums['getCallsOnHoldData'] = current_calls_on_hold_checksum
            logger.info("Checksum para 'getCallsOnHoldData' ha cambiado.")

        if current_live_queue_status_checksum != _last_data_checksums['liveQueueStatus']:
            data_changed = True
            _last_data_checksums['liveQueueStatus'] = current_live_queue_status_checksum
            logger.info("Checksum para 'liveQueueStatus' ha cambiado.")

        if data_changed:
            async_to_sync(channel_layer.group_send)(
                "calls",
                {
                    "type": "dataUpdate",
                    "payload": full_frontend_payload
                }
            )
            logger.info("[Celery] Datos cambiaron, emitido a clientes WebSocket.")
        else:
            logger.info("[Celery] Sin cambios en los datos, no se emitió a clientes WebSocket.")

    except Exception as e:
        logger.exception(f"Error en Celery broadcast_calls_update: {e}") # Usar logger.exception para incluir traceback




@shared_task
def log_system_metrics():
    try:
        metrics = get_resource_metrics()
        logger.info(f"[Metrics] RAM: {metrics['memory_used_mb']:.2f} MB ({metrics['memory_percent']:.2f}%), CPU: {metrics['cpu_percent']:.2f}%")
    except Exception as e:
        logger.exception("Error en Celery log_system_metrics:")