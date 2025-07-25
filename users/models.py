# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('agent', 'Agent'),
        ('teamleader', 'Team Leader'),
        ('supervisor', 'Supervisor'),
        ('egs', 'EGS'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, blank=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    extension = models.CharField(max_length=10, blank=True, null=True)
    queues = models.ManyToManyField('queues.Queue', related_name='users', blank=True)

    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"
