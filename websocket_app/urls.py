from django.urls import path
from .views import system_metrics_view, LiveQueueStatusAPIView

urlpatterns = [
    path('metrics/', system_metrics_view, name='system_metrics'),
    path('live-queue-status/', LiveQueueStatusAPIView.as_view(), name='live_queue_status_api'),
]
