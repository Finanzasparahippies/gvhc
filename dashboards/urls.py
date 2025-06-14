# dashboards/urls.py
from django.urls import path
from .views import SharpenApiProxyView

urlpatterns = [
    # ... otras urls
    path('proxy/sharpen-query/', SharpenApiProxyView.as_view(), name='sharpen-proxy'),
]