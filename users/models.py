# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone # Importa timezone
import logging

logger = logging.getLogger(__name__)

class User(AbstractUser):

    ROLE_CHOICES = [
        ('agent', 'Agent'),
        ('teamleader', 'Team Leader'),
        ('supervisor', 'Supervisor'),
        ('egs', 'EGS'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, blank=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    extension = models.CharField(max_length=10, blank=True, null=True)
    queues = models.ManyToManyField('queues.Queue', related_name='users', blank=True)
    sharpen_username = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        help_text="Username del agente en Sharpen, para asociar métricas."
    )
    gamification_points = models.IntegerField(
        default=0,
        help_text="Puntos de gamificación acumulados por el agente."
    )
    gamification_level = models.IntegerField(
        default=1,
        help_text="Nivel actual de gamificación del agente."
    )
    # Puedes añadir más campos, por ejemplo:
    last_point_update = models.DateTimeField(null=True, blank=True)
    last_calls_handled = models.IntegerField(
        default=0,
        help_text="Último conteo de llamadas manejadas obtenido de Sharpen."
    )
    last_quality_score = models.FloatField( # Usar FloatField si puede tener decimales
        default=0.0,
        help_text="Última puntuación de calidad obtenida de Sharpen."
    )
    last_resolution_rate = models.FloatField(
        default=0.0,
        help_text="Última tasa de resolución obtenida de Sharpen."
    )
    
    # Un flag para bonos únicos (ej. el bono de "nuevo agente")
    first_processed_gamification_data = models.BooleanField(
        default=False,
        help_text="Indica si los datos de gamificación de este agente ya han sido procesados al menos una vez."
    )
    total_calls_handled = models.IntegerField(default=0)
    average_handle_time = models.IntegerField(default=0) # en segundos

    def __str__(self):
        return self.username or self.email or "Usuario sin nombre"

    # Método para subir de nivel
    def check_level_up(self):
        # Define tus umbrales de puntos para cada nivel
        level_thresholds = {
            1: 0,
            2: 100,
            3: 250,
            4: 500,
            5: 1000,
            # Añade más niveles según sea necesario
        }
        
        # Encuentra el nivel más alto que el usuario ha alcanzado con sus puntos actuales
        new_level = self.gamification_level
        for level, threshold in level_thresholds.items():
            if self.gamification_points >= threshold:
                new_level = max(new_level, level) # Asegura que siempre suba, no baje
            
        if new_level > self.gamification_level:
            old_level = self.gamification_level
            self.gamification_level = new_level
            self.save(update_fields=['gamification_level'])
            print(f"¡{self.username} subió al nivel {self.gamification_level}!")
            # TODO: Considera emitir un evento de WebSocket aquí para notificar al frontend
            # Para esto, necesitarías:
            # from channels.layers import get_channel_layer
            # from asgiref.sync import async_to_sync
            # channel_layer = get_channel_layer()
            # if channel_layer:
            #     async_to_sync(channel_layer.group_send)(
            #         f"user_{self.id}", # O un grupo global si quieres que todos vean las notificaciones de subida de nivel
            #         {
            #             "type": "gamification_level_up", # Un tipo de evento que tu consumer reconozca
            #             "payload": {
            #                 "user_id": self.id,
            #                 "username": self.username,
            #                 "old_level": old_level,
            #                 "new_level": self.gamification_level,
            #                 "message": f"¡Felicidades, {self.username}! Has subido al nivel {self.gamification_level}."
            #             }
            #         }
            #     )
            return True
        return False

    def add_points(self, points: int):
        from django.db.models import F

        self.gamification_points = F('gamification_points') + points
        self.save(update_fields=['gamification_points'])
        print(f"Puntos añadidos a {self.username}. Total: {self.gamification_points}")
        # Después de añadir puntos, verifica si sube de nivel
        self.refresh_from_db()
        logger.info(f"Puntos añadidos a {self.username}. Total: {self.gamification_points}")

        self.check_level_up()
    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"
