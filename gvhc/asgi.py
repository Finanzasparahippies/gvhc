"""
ASGI config for gvhc project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gvhc.settings")
from channels.auth import AuthMiddlewareStack # <-- Este es el middleware de autenticación de Channels
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.sessions import SessionMiddlewareStack # <-- Este es el de sesión
from websocket_app import routing
from .jwt_middleware import JWTAuthMiddleware

# from channels.security.websocket import AllowedHostsOriginValidator, OriginValidator


django_asgi_app = get_asgi_application()

# 2. Define las rutas de WebSocket
websocket_app = URLRouter(routing.websocket_urlpatterns)

# 3. Combina todo en un ProtocolTypeRouter
# Esto maneja las solicitudes HTTP y WebSocket
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": SessionMiddlewareStack(  # <-- Paso 1: Primero el SessionMiddleware
        JWTAuthMiddleware(  # <-- Paso 2: Luego tu middleware de JWT
            AuthMiddlewareStack( # <-- Paso 3: Luego el de autenticación de Channels
                websocket_app
            )
        )
    ),
})