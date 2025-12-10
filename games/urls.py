from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    # Auth
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Profile
    path('profile/', views.get_profile, name='profile'),
    path('history/', views.get_game_history, name='game_history'),
    
    # Coin requests
    path('coins/request/', views.request_coins, name='request_coins'),
    path('coins/my-requests/', views.my_coin_requests, name='my_coin_requests'),
    
    # Admin
    path('admin/pending-requests/', views.admin_pending_requests, name='admin_pending_requests'),
    path('admin/approve/<int:request_id>/', views.admin_approve_request, name='admin_approve'),
    path('admin/deny/<int:request_id>/', views.admin_deny_request, name='admin_deny'),
    
    # Games
    path('games/blackjack/', views.play_blackjack, name='play_blackjack'),
    path('games/poker/', views.play_poker, name='play_poker'),
    path('games/roulette/', views.play_roulette, name='play_roulette'),
    path('games/dice/', views.play_dice, name='play_dice'),
    path('games/minesweeper/', views.play_minesweeper, name='play_minesweeper'),
    
    # Educational content
    path('education/', views.gambling_education, name='gambling_education'),
]
