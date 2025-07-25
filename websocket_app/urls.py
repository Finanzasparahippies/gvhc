from django.urls import path
from .views import system_metrics_view

urlpatterns = [
    path('metrics/', system_metrics_view, name='system_metrics'),
]
