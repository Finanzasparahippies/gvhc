# users/views.py
from rest_framework import generics, permissions
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User # Renombra si tienes conflicto con django.contrib.auth.models.User
from .serializers import UserSerializer
import logging
from django.db.models import F
# from django.contrib.auth.models import User 
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import MyTokenObtainPairSerializer

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        logger.info(username, password)

        user = authenticate(request, username=username, password=password)
        if not user:
            logger.warning(f"Fallo de autenticación para: {username}")
            return Response({"error": "Invalid credentials"}, status=401)

        refresh = RefreshToken.for_user(user)
        user_data = UserSerializer(user).data

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': user_data
        })

class RegisterView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if UserOne.objects.filter(username=username).exists():
            return Response({"error": "User already exists"}, status=400)

        user = UserOne.objects.create_user(username=username, password=password)
        return Response({"message": "User created successfully"})

class ProtectedUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

def ping(request):
    return JsonResponse({'status': 'ok'})

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

    logger.info(f"MyTokenObtainPairView loaded with serializer: {serializer_class}")

class AgentGamificationListView(generics.ListAPIView):
    """
    API para listar a todos los agentes con sus puntos y niveles de gamificación.
    Solo accesible por administradores o supervisores.
    """
    queryset = User.objects.filter(is_staff=True).order_by('-gamification_points') # O filtrar por un rol específico de agente
    serializer_class = UserSerializer # Asegúrate que este serializer incluya gamification_points y gamification_level
    permission_classes = [permissions.IsAuthenticated] # O IsAdminUser/IsSupervisor

    def get_queryset(self):
        # Si quieres filtrar solo por agentes, ajusta esto.
        # Por ejemplo, podrías tener un campo 'is_agent' en tu modelo User.
        return super().get_queryset()

class MyGamificationDetailView(generics.RetrieveAPIView):
    """
    API para que un agente vea sus propios puntos y nivel de gamificación.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user # Devuelve el usuario actualmente autenticado

class GamificationLeaderboardView(generics.ListAPIView):
    """
    API para mostrar la tabla de clasificación de agentes por puntos.
    """
    queryset = User.objects.filter(gamification_level__gt=0).order_by('-gamification_points', 'username')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated] # O IsAuthenticatedOrReadOnly si es público
    # Podrías añadir paginación si hay muchos usuarios:
    # pagination_class = YourCustomPaginationClass # Define una paginación si es necesario
