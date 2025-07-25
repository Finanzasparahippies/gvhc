# users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = [
            'username', 'password1', 'password2', 'role', 'first_name', 
            'last_name', 'email', 'extension', 'queues', 'is_staff', 'is_active'
        ]

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = [
            'username', 'role', 'first_name', 'last_name', 'email', 
            'extension', 'queues', 'is_staff', 'is_active', 'last_login'
        ]
