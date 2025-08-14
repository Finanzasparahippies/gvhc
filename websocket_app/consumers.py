# websocket_app/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
import logging
from .fetch_script import fetch_calls_on_hold_data, fetch_live_queue_status_data
import asyncio

logger = logging.getLogger(__name__)

class CallsConsumer(AsyncWebsocketConsumer):
    """
    Este consumer maneja las conexiones WebSocket para las actualizaciones de llamadas.
    """

    async def send_heartbeat(self):
        while True:
            try:
                await asyncio.sleep(20)  # cada 20 segundos
                await self.send(text_data=json.dumps({"type": "heartbeat"}))
                logger.debug(f"💓 Heartbeat enviado a {self.channel_name}")
            except asyncio.CancelledError:
                logger.info(f"⛔ Heartbeat cancelado para {self.channel_name}")
                break
            except Exception as e:
                logger.error(f"❌ Error en heartbeat: {e}")
                break


    async def connect(self):
        self.group_name = "calls"  # Nombre del grupo para broadcast

        await self.accept()
        await self.send(text_data=json.dumps({"message": "WebSocket conectado"}))
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        

        logger.info(f"Cliente conectado al grupo '{self.group_name}' con channel_name: {self.channel_name}")
        
        self.heartbeat_task = asyncio.create_task(self.send_heartbeat())

        try:            
            calls_on_hold_data = await fetch_calls_on_hold_data()
            live_queue_status_data = await fetch_live_queue_status_data()

            calls_data = calls_on_hold_data.get("data") or calls_on_hold_data.get("getCallsOnHoldData") or []
            live_queue_data = live_queue_status_data.get("data") or live_queue_status_data.get("liveQueueStatus") or []

            initial_payload = {
                "getCallsOnHoldData": calls_data,
                "getLiveQueueStatusData": live_queue_data
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
        if hasattr(self, "heartbeat_task"):
            self.heartbeat_task.cancel()


    async def receive(self, text_data):
        """
        Este método maneja los mensajes recibidos del cliente WebSocket.
        Responde con un 'pong' si recibe un 'ping'.
        """
        try:
            data = json.loads(text_data)
            if data.get('type') == 'ping':
                # Si el cliente envía un 'ping', responde con un 'pong'
                await self.send(text_data=json.dumps({'type': 'pong'}))
                logger.debug("Received ping, sent pong.")
            # Puedes añadir aquí cualquier otra lógica para manejar diferentes tipos de mensajes
            # Por ejemplo, si el frontend necesita enviar comandos.
        except json.JSONDecodeError:
            logger.error("Received non-JSON data on WebSocket.")
        except Exception as e:
            logger.error(f"Error handling received message: {e}")
    
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
