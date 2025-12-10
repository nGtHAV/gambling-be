from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, GameHistory, CoinRequest


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_staff']


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    is_bankrupt = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = ['user', 'coins', 'total_wagered', 'total_won', 'total_lost', 
                  'games_played', 'is_bankrupt', 'created_at']
    
    def get_is_bankrupt(self, obj):
        return obj.is_bankrupt()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True, min_length=6)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm']
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password": "Passwords do not match"})
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        return user


class GameHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = GameHistory
        fields = ['id', 'game_type', 'bet_amount', 'won', 'payout', 'details', 'created_at']


class CoinRequestSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    reviewed_by = UserSerializer(read_only=True)
    
    class Meta:
        model = CoinRequest
        fields = ['id', 'user', 'amount', 'reason', 'status', 'reviewed_by', 
                  'created_at', 'reviewed_at']
        read_only_fields = ['status', 'reviewed_by', 'reviewed_at']


class CoinRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoinRequest
        fields = ['amount', 'reason']


# Game-specific serializers
class BlackjackActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['deal', 'hit', 'stand', 'double'])
    bet = serializers.IntegerField(min_value=1)
    game_state = serializers.JSONField(required=False, allow_null=True)


class PokerActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['deal', 'draw'])
    bet = serializers.IntegerField(min_value=1)
    hold_indices = serializers.ListField(
        child=serializers.IntegerField(min_value=0, max_value=4),
        required=False,
        default=[]
    )
    game_state = serializers.JSONField(required=False, allow_null=True)


class RouletteActionSerializer(serializers.Serializer):
    bet_type = serializers.ChoiceField(
        choices=['number', 'color', 'odd_even', 'high_low', 'dozen', 'column']
    )
    bet_value = serializers.JSONField()  # Can be int or string depending on bet type
    bet = serializers.IntegerField(min_value=1)


class DiceActionSerializer(serializers.Serializer):
    bet_type = serializers.ChoiceField(
        choices=['exact', 'over', 'under', 'odd_even', 'seven']
    )
    bet_value = serializers.JSONField()
    bet = serializers.IntegerField(min_value=1)


class MinesweeperActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['create', 'reveal', 'cashout'])
    bet = serializers.IntegerField(min_value=1)
    grid_size = serializers.IntegerField(min_value=3, max_value=8, default=5)
    num_mines = serializers.IntegerField(min_value=1, max_value=24, default=5)
    tile_index = serializers.IntegerField(required=False, min_value=0)
    game_state = serializers.JSONField(required=False, allow_null=True)
