from rest_framework import viewsets, permissions
from .models import Vendor, Dish, Order
from .serializers import VendorSerializer, DishSerializer, OrderSerializer

class VendorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Vendor.objects.filter(active=True)
    serializer_class = VendorSerializer
    permission_classes = [permissions.AllowAny]

class DishViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Dish.objects.all()
    serializer_class = DishSerializer
    permission_classes = [permissions.AllowAny]

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
