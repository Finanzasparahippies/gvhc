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
from users.views import MyTokenObtainPairView, ProtectedUserView # <-- Aquí está el cambio clave si no lo tienes así
from websocket_app.views import cors_test
from rest_framework_simplejwt.views import (
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
            "grammar": "/api/grammar/",
            "reports": "/api/reports/",
            "dashboards": "/api/dashboards",
            "websocket": "/api/websocket/",
            "foodstation": "/api/foodstation/",
            "cors_test": "/cors-test/",
        }
    })

urlpatterns = [
    path('', root_view, name='root'), 
    path('protected/', ProtectedUserView.as_view(), name='protected'),
    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path("admin/", admin.site.urls),
    path('api/', include('users.urls')),
    path('api/', include('faqs.urls') ),
    path('api/grammar/', include('calling_monitor.urls')),
    path('api/reports/', include('reports.urls')),
    path('api/dashboards/', include('dashboards.urls')),
    path('api/websocket/', include('websocket_app.urls')),
    path("cors-test/", cors_test),
    path('api/foodstation/', include('foodstation.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

