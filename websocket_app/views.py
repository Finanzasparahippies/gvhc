from django.shortcuts import render

# Create your views here.

import asyncio
from websocket_app.task import broadcast_calls_update

asyncio.run(broadcast_calls_update())
