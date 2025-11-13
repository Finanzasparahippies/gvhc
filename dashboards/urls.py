# dashboards/urls.py
from django.urls import path
from .views import SharpenApiGenericProxyView, SharpenAudioProxyView
from .views_quotes import fetch_quote
from .views_news import news_list

urlpatterns = [
    # ... otras urls
    # path('proxy/sharpen-query/', SharpenApiProxyView.as_view(), name='sharpen-proxy'),
    path('proxy/generic/', SharpenApiGenericProxyView.as_view(), name='sharpen_generic_proxy'),
    path('sharpen/audio/', SharpenAudioProxyView.as_view(), name='sharpen_audio_proxy'),
    path('quote/', fetch_quote, name='quote'),
    path('news/', news_list, name='news_list'),
]

