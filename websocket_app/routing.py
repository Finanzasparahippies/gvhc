# gvhc/routing.py

from django.urls import re_path
from . import consumers  # Reemplaza 'yourapp' por el nombre real de tu app

websocket_urlpatterns = [
    re_path(r"^ws/calls/$", consumers.MyConsumer.as_asgi()),
]
