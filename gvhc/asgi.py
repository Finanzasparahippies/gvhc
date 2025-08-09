"""
ASGI config for gvhc project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from websocket_app import routing
from .jwt_middleware import JWTAuthMiddleware

# from channels.security.websocket import AllowedHostsOriginValidator, OriginValidator

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gvhc.settings")

django_asgi_app = get_asgi_application()

# 2. Define las rutas de WebSocket
websocket_app = URLRouter(routing.websocket_urlpatterns)

# 3. Combina todo en un ProtocolTypeRouter
# Esto maneja las solicitudes HTTP y WebSocket
application_without_middleware = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": websocket_app,
})

# 4. Aplica el middleware a toda la aplicación
# Ahora, JWTAuthMiddleware se ejecutará después de que Django se haya inicializado
application = JWTAuthMiddleware(application_without_middleware)