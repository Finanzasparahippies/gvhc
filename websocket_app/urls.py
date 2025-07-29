from django.urls import path
from asgiref.sync import sync_to_async 
from .views import system_metrics_view, get_calls_on_hold_from_sharpen, LiveQueueStatusAPIView

urlpatterns = [
    path('metrics/', system_metrics_view, name='system_metrics'),
    path('pacientes-en-espera/', get_calls_on_hold_from_sharpen, name='pacientes_en_espera'),
    path('live-queue-status/', sync_to_async(LiveQueueStatusAPIView.as_view()), name='live_queue_status_api'),
]
