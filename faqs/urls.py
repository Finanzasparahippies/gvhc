from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AnswerViewSet, FaqViewSet, search_faqs, EventViewSet, get_departments

router = DefaultRouter()
router.register(r'answers', AnswerViewSet)
router.register(r'faqs', FaqViewSet)
router.register(r'events', EventViewSet)

urlpatterns = [
    path('search/', search_faqs, name='faq-search'),
    path('departments/', get_departments, name='departments-list'), # Nuevo endpoint
    *router.urls,
]


