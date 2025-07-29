# websocket_app/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
import logging

logger = logging.getLogger(__name__)

class CallsConsumer(AsyncWebsocketConsumer):
    """
    Este consumer maneja las conexiones WebSocket para las actualizaciones de llamadas.
    """
    async def connect(self):
        self.group_name = "calls"  # Nombre del grupo para broadcast

        # Unirse al grupo de canales
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()

        print(f"Cliente conectado al grupo '{self.group_name}' con channel_name: {self.channel_name}")
        
        # Enviar mensaje de confirmación de conexión
        await self.send(text_data=json.dumps({"message": "WebSocket conectado"}))

    async def disconnect(self, close_code):
        # Salir del grupo de canales al desconectar
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        logger.info(f"Cliente desconectado del grupo '{self.group_name}' con código: {close_code}.") # Log close_code

    async def send_calls(self, event):
        """
        Este método es invocado por la tarea de Celery.
        Recibe el payload y lo retransmite al cliente WebSocket en el formato esperado.
        """
        payload = event.get('payload', {})
        
        # Formatear el mensaje como lo espera el frontend
        await self.send(text_data=json.dumps({
            "type": "callsUpdate",  # El tipo de mensaje que el hook de React reconoce
            "payload": payload
        }))
        logger.debug(f"Enviando actualización de llamadas al cliente {self.channel_name}. Payload size: {len(json.dumps(payload))} bytes.") # Use debug for verbose data sending
