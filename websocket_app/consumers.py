# websocket_app/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
import logging
from .fetch_script import fetch_calls_on_hold_data, fetch_live_queue_status_data

logger = logging.getLogger(__name__)

class CallsConsumer(AsyncWebsocketConsumer):
    """
    Este consumer maneja las conexiones WebSocket para las actualizaciones de llamadas.
    """
    async def connect(self):
        self.group_name = "calls"  # Nombre del grupo para broadcast

        await self.accept()
        # Unirse al grupo de canales
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        

        logger.info(f"Cliente conectado al grupo '{self.group_name}' con channel_name: {self.channel_name}")
        
        # Enviar mensaje de confirmación de conexión
        await self.send(text_data=json.dumps({"message": "WebSocket conectado"}))
        try:            
            calls_on_hold_data = await fetch_calls_on_hold_data()
            live_queue_status_data = await fetch_live_queue_status_data()

            initial_payload = {
                "getCallsOnHoldData": calls_on_hold_data.get('getCallsOnHoldData', []),
                "getLiveQueueStatusData": live_queue_status_data.get('liveQueueStatus', [])
            }
            
            await self.send(text_data=json.dumps({
                "type": "dataUpdate",
                "payload": initial_payload
            }))
            logger.info(f"Enviado estado inicial de datos al nuevo cliente: {self.channel_name}")

        except Exception as e:
            logger.error(f"Error al enviar datos iniciales a nuevo cliente: {e}", exc_info=True)
        # --- FIN DE LA MODIFICACIÓN ---

    async def disconnect(self, close_code):
        # Salir del grupo de canales al desconectar
        logger.info(f"Cliente desconectado del grupo '{self.group_name}' con código: {close_code}.")
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # No specific receive logic needed if it's just for broadcasting
        pass
    
    async def dataUpdate(self, event):
        """
        Este método es invocado por la tarea de Celery.
        Recibe el payload y lo retransmite al cliente WebSocket en el formato esperado.
        """
        payload = event.get('payload', {})
        
        # Formatear el mensaje como lo espera el frontend
        await self.send(text_data=json.dumps({
            "type": "dataUpdate",  # El tipo de mensaje que el hook de React reconoce
            "payload": payload
        }))
        logger.debug(f"Enviando actualización de llamadas al cliente {self.channel_name}. Payload size: {len(json.dumps(payload))} bytes.") # Use debug for verbose data sending
