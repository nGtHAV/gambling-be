from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """Extended user profile with coin balance"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    coins = models.IntegerField(default=1000)
    total_wagered = models.IntegerField(default=0)
    total_won = models.IntegerField(default=0)
    total_lost = models.IntegerField(default=0)
    games_played = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.coins} coins"
    
    def is_bankrupt(self):
        return self.coins <= 0


class GameHistory(models.Model):
    """Track all game results"""
    GAME_CHOICES = [
        ('blackjack', 'Blackjack'),
        ('poker', 'Poker'),
        ('roulette', 'Roulette'),
        ('dice', 'Dice'),
        ('minesweeper', 'Minesweeper'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='game_history')
    game_type = models.CharField(max_length=20, choices=GAME_CHOICES)
    bet_amount = models.IntegerField()
    won = models.BooleanField()
    payout = models.IntegerField()  # Amount won/lost (negative if lost)
    details = models.JSONField(default=dict)  # Store game-specific details
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        result = "Won" if self.won else "Lost"
        return f"{self.user.username} - {self.game_type} - {result} {abs(self.payout)} coins"


class CoinRequest(models.Model):
    """Request for more coins when bankrupt"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('denied', 'Denied'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coin_requests')
    amount = models.IntegerField(default=1000)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='reviewed_requests'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.amount} coins - {self.status}"


# Signal to create UserProfile when User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
