from django.db import models
from django.contrib.auth import get_user_model
from cloudinary.models import CloudinaryField  # o ImageField si no usas Cloudinary

# Create your models here.
User = get_user_model()

class Vendor(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    phone = models.CharField(max_length=15, blank=True, help_text="Vendor phone number")
    contact_email = models.EmailField()
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Dish(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='dishes')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    image = CloudinaryField('image', blank=True, null=True)  # o models.ImageField(upload_to='dishes/')
    available_days = models.CharField(
        max_length=100, 
        help_text="Días disponibles (ej: monday,tuesday,wednesday)"
    )
    start_time = models.TimeField(help_text="First time to order")
    end_time = models.TimeField(help_text="Last time to order")
    restriction = models.TextField(blank=True, help_text="Vendor restrictions (ej: vegetarian, gluten-free)")

    def __str__(self):
        return f"{self.name} ({self.vendor.name})"

    
class DishVariation(models.Model):
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE, related_name='variations')
    name = models.CharField(max_length=100, help_text="Nombre de la variedad, ej: Salseado, Sin salsa, Picante")
    extra_price = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)

    def __str__(self):
        return f"{self.name} ({self.dish.name})"

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE)
    variation = models.ForeignKey(DishVariation, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, help_text="Comentarios del usuario")
    sent_to_vendor = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user} pidió {self.quantity} x {self.dish.name}"