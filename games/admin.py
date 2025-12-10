from django.contrib import admin
from django.utils import timezone
from .models import UserProfile, GameHistory, CoinRequest


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'coins', 'total_wagered', 'total_won', 'total_lost', 'games_played', 'created_at']
    search_fields = ['user__username', 'user__email']
    list_filter = ['created_at']
    readonly_fields = ['created_at']


@admin.register(GameHistory)
class GameHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'game_type', 'bet_amount', 'won', 'payout', 'created_at']
    list_filter = ['game_type', 'won', 'created_at']
    search_fields = ['user__username']
    readonly_fields = ['created_at']


@admin.register(CoinRequest)
class CoinRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'status', 'reviewed_by', 'created_at', 'reviewed_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'reason']
    readonly_fields = ['created_at']
    actions = ['approve_requests', 'deny_requests']
    
    def approve_requests(self, request, queryset):
        for coin_request in queryset.filter(status='pending'):
            coin_request.status = 'approved'
            coin_request.reviewed_by = request.user
            coin_request.reviewed_at = timezone.now()
            coin_request.save()
            # Add coins to user
            profile = coin_request.user.profile
            profile.coins += coin_request.amount
            profile.save()
        self.message_user(request, f"Approved {queryset.count()} coin requests")
    approve_requests.short_description = "Approve selected coin requests"
    
    def deny_requests(self, request, queryset):
        queryset.filter(status='pending').update(
            status='denied',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f"Denied {queryset.count()} coin requests")
    deny_requests.short_description = "Deny selected coin requests"
