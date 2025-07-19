# dashboards/urls.py
from django.urls import path
from .views import SharpenApiGenericProxyView, SharpenAudioProxyView
from .views_quotes import fetch_quote

urlpatterns = [
    # ... otras urls
    # path('proxy/sharpen-query/', SharpenApiProxyView.as_view(), name='sharpen-proxy'),
    path('proxy/generic/', SharpenApiGenericProxyView.as_view(), name='sharpen_generic_proxy'),
    path('sharpen/audio/', SharpenAudioProxyView.as_view(), name='sharpen_audio_proxy'),
    path('quote/', fetch_quote, name='quote'),
]

