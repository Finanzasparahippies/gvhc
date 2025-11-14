from django.db import models

# Create your models here.
from django.db import models
from cloudinary.models import CloudinaryField

class News(models.Model):
    LEVEL_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ]
    title = models.CharField(max_length=255)
    summary = models.TextField(blank=True, null=True)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, help_text="Nivel de importancia de la noticia")
    url = models.URLField(max_length=500, blank=True, null=True)
    image = CloudinaryField('image', blank=True, null=True)
    published_at = models.DateTimeField()
    source = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.published_at.strftime('%Y-%m-%d %H:%M')})"
