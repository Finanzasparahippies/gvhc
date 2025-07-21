from django.urls import path
from . import views

urlpatterns = [
    path('procesar/', views.procesar_reporte, name='procesar_reporte'),
    
]
