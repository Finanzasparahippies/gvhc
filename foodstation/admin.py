# foodstation/admin.py
from django.contrib import admin
from .models import Vendor, Dish, Order, DishVariation

admin.site.register(Vendor)
admin.site.register(Dish)
admin.site.register(DishVariation)
admin.site.register(Order)
