from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AnswerViewSet, FaqViewSet, search_faqs, EventViewSet

router = DefaultRouter()
router.register(r'answers', AnswerViewSet)
router.register(r'faqs', FaqViewSet)
router.register(r'events', EventViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('search/', search_faqs, name='search_faqs'),
]


