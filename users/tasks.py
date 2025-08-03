# users/tasks.py
import logging
from celery import shared_task
from django.db import transaction
from django.conf import settings
from users.models import User  # Importa tu modelo de usuario
from websocket_app.fetch_script import fetch_agent_performance_data # Necesitarás crear esta función
import time # Para simular retardo si es necesario

logger = logging.getLogger(__name__)

@shared_task
def update_agent_gamification_scores():
    logger.info("Iniciando tarea de actualización de gamificación de agentes...")
    try:
        # Obtener datos de rendimiento de Sharpen
        # Asumiendo que fetch_agent_performance_data es async, necesitas async_to_sync si no estás en un contexto asincrono
        # Si fetch_agent_performance_data es una simple función síncrona, úsala directamente.
        from asgiref.sync import async_to_sync
        sharpen_data = async_to_sync(fetch_agent_performance_data)()

        for agent_data in sharpen_data:
            sharpen_username = agent_data.get('username') # Asegúrate de que esta clave coincida con la API de Sharpen
            if not sharpen_username:
                logger.warning(f"Dato de agente sin username de Sharpen. Saltando: {agent_data}")
                continue

            try:
                # Buscar el usuario Django asociado
                user = User.objects.get(sharpen_username=sharpen_username)

                # Define tu lógica de puntos aquí
                # Ejemplo: 10 puntos por llamada manejada + 1 punto por cada punto de calidad
                points_to_add = (
                    agent_data.get('calls_handled_today', 0) * 10 +
                    agent_data.get('quality_score', 0) * 1
                    # Añade más criterios:
                    # + (agent_data.get('issue_resolution_rate', 0) * 50)
                )

                if points_to_add > 0:
                    with transaction.atomic(): # Asegura que la operación sea atómica
                        user.add_points(points_to_add)
                        logger.info(f"Agregados {points_to_add} puntos a {user.username}. Total: {user.gamification_points}. Nivel: {user.gamification_level}")
                else:
                    logger.info(f"No hay puntos que añadir para {user.username} en esta ronda.")

            except User.DoesNotExist:
                logger.warning(f"Usuario Django no encontrado para Sharpen username: {sharpen_username}. Saltando.")
            except Exception as e:
                logger.error(f"Error procesando datos para Sharpen username {sharpen_username}: {e}")

    except Exception as e:
        logger.exception(f"Error general en update_agent_gamification_scores: {e}")