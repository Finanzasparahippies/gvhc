from rest_framework.routers import DefaultRouter
from .views import VendorViewSet, DishViewSet, OrderViewSet
from django.urls import path, include

router = DefaultRouter()
router.register('vendors', VendorViewSet)
router.register('dishes', DishViewSet)
router.register('orders', OrderViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
