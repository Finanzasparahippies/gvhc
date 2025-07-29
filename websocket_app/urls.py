from django.urls import path
from .views import system_metrics_view, get_calls_on_hold, LiveQueueStatusAPIView

urlpatterns = [
    path('metrics/', system_metrics_view, name='system_metrics'),
    path('pacientes-en-espera/', get_calls_on_hold, name='pacientes_en_espera'),
    path('live-queue-status/', LiveQueueStatusAPIView.as_view(), name='live_queue_status_api'),
]
