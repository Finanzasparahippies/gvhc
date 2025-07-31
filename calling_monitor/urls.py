#calling_monitor/urls.py
from django.urls import path
from .views import process_call, grammar_correction2, analyze_sharpen_audio

urlpatterns = [
    path('process_call/', process_call, name='grammar_correction'),
    path('correct-grammar2/', grammar_correction2, name='grammar_correction2'),
    path('analyze_remote_audio/', analyze_sharpen_audio, name='analyze_remote_audio'),
]
