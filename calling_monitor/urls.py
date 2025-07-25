from django.urls import path
from .views import grammar_correction, grammar_correction2

urlpatterns = [
    path('correct-grammar/', grammar_correction, name='grammar_correction'),
    path('correct-grammar2/', grammar_correction2, name='grammar_correction2'),
]
