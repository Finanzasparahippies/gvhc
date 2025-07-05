# users/serializers.py
from django.contrib.auth import authenticate
from rest_framework import serializers
from .models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import logging

logger = logging.getLogger(__name__)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'role', 'email', 'first_name', 'last_name']

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        logger.info("--- MyTokenObtainPairSerializer.validate started ---")
        logger.info(f"Received attributes for validation: {attrs}")
        print({attrs})

        username = attrs.get("username")
        password = attrs.get("password")

        user = authenticate(username=username, password=password)

        if user is None:
            logger.warning("⚠️ Autenticación fallida en MyTokenObtainPairSerializer")
            raise serializers.ValidationError("Credenciales inválidas")

        # Asigna self.user explícitamente
        self.user = user

        validated_data  = super().validate(attrs)  # Esto generará access y refresh token
        validated_data.update({
            'user': UserSerializer(user).data
        })
        # Incluye los datos del usuario serializado

        logger.info(f"Final response data: {validated_data}")
        logger.info("--- MyTokenObtainPairSerializer.validate finished ---")

        return validated_data