from django.urls import path
from .views import LoginView, RegisterView, ProtectedUserView

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('protected/', ProtectedUserView.as_view(), name='protected'), 

]

