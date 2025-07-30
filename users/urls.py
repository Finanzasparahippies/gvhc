from django.urls import path
from .views import RegisterView, ProtectedUserView, ping, AgentGamificationListView, MyGamificationDetailView, GamificationLeaderboardView

urlpatterns = [
    # path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('protected/', ProtectedUserView.as_view(), name='protected'),
    path('ping/', ping, name='ping'), 
    path('agents/', AgentGamificationListView.as_view(), name='agent-gamification-list'),
    path('my-score/', MyGamificationDetailView.as_view(), name='my-gamification-score'),
    path('leaderboard/', GamificationLeaderboardView.as_view(), name='gamification-leaderboard'),
]
