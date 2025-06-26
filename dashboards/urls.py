# dashboards/urls.py
from django.urls import path
from .views import SharpenApiGenericProxyView, ProxyRecordingView, ProxyOldRecordingByMixmonView

urlpatterns = [
    # ... otras urls
    # path('proxy/sharpen-query/', SharpenApiProxyView.as_view(), name='sharpen-proxy'),
    path('proxy/generic/', SharpenApiGenericProxyView.as_view(), name='sharpen_generic_proxy'),
    path('proxy/recording/<str:recording_key>/', ProxyRecordingView.as_view()),
    path('dashboards/proxy/old-recording/<str:mixmon_file_name>/', ProxyOldRecordingByMixmonView.as_view(), name='proxy-old-recording-by-mixmon'),
]

