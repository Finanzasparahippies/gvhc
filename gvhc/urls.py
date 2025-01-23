"""
URL configuration for gvhc project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.http import JsonResponse
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from users.views import ProtectedUserView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)

def root_view(request):
    return JsonResponse({
        "message": "Bienvenido a la API de GVHC",
        "available_endpoints": {
            "tokens": "/api/token/",
            "users": "/api/",
            "answers": "/api/answers/",
            "grammar": "/api/grammar/"
        }
    })

urlpatterns = [
    path('', root_view, name='root'), 
    path('protected/', ProtectedUserView, name='protected'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path("admin/", admin.site.urls),
    path('api/', include('users.urls')),
    path('api/answers/', include('faqs.urls') ),
    path('api/grammar/', include('calling_monitor.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
