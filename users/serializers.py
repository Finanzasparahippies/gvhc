# users/serializers.py
from django.contrib.auth import authenticate
from rest_framework import serializers
from .models import User
from queues.models import Queue
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import logging
import time


logger = logging.getLogger(__name__)

class QueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Queue
        fields = ['id', 'name']  # o los campos que necesites

class UserSerializer(serializers.ModelSerializer):
    queues = QueueSerializer(many=True, read_only=True)
    class Meta:
        model = User
        fields = ['id', 'username', 'role', 'email', 'first_name', 'last_name', 'queues']

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        start = time.time()

        # --- La línea del error estaba aquí ---
        logger.info("--- MyTokenObtainPairSerializer.validate started ---")
        # Esta es la forma correcta de imprimir para depurar:
        logger.info(f"Received attributes for validation: {attrs}")

        # Ejecuta la validación original (comprueba usuario y contraseña)
        data = super().validate(attrs)
        end = time.time()

        # Ahora, añade los datos de tu usuario a la respuesta
        # self.user es el objeto de usuario que se autenticó correctamente
        user_data = UserSerializer(self.user).data
        data['user'] = user_data
        print(f"Validation took {end - start} seconds")
        # La respuesta ahora contendrá: refresh, access, y user
        return data

    @classmethod
    def get_token(cls, user):
        # Esta función añade datos DENTRO del token JWT (payload) si lo necesitas.
        # Por ejemplo, para añadir el username al payload del token.
        token = super().get_token(user)

        # Añadir campos personalizados al payload del token
        token['username'] = user.username
        # ... puedes añadir más campos aquí

        return token