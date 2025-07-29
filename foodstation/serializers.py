from rest_framework import serializers
from .models import Vendor, Dish, Order, DishVariation

class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = '__all__'

class DishVariationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DishVariation
        fields = ['id', 'name', 'extra_price']

class DishSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    image_url = serializers.SerializerMethodField()
    variations = DishVariationSerializer(many=True, read_only=True)

    def get_image_url(self, obj):
        return obj.image.url if obj.image else None
    
    class Meta:
        model = Dish
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['user', 'sent_to_vendor', 'created_at']
