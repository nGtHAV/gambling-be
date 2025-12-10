from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.utils import timezone

from .models import UserProfile, GameHistory, CoinRequest
from .serializers import (
    UserProfileSerializer, RegisterSerializer, GameHistorySerializer,
    CoinRequestSerializer, CoinRequestCreateSerializer,
    BlackjackActionSerializer, PokerActionSerializer, RouletteActionSerializer,
    DiceActionSerializer, MinesweeperActionSerializer
)
from .game_logic import BlackjackGame, PokerGame, RouletteGame, DiceGame, MinesweeperGame


# Auth Views
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'profile': UserProfileSerializer(user.profile).data
        }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile(request):
    """Get current user's profile"""
    profile = request.user.profile
    return Response(UserProfileSerializer(profile).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_game_history(request):
    """Get user's game history"""
    history = GameHistory.objects.filter(user=request.user)[:50]
    return Response(GameHistorySerializer(history, many=True).data)


# Coin Request Views
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_coins(request):
    """Request more coins (when bankrupt)"""
    profile = request.user.profile
    
    # Check if user has pending request
    pending = CoinRequest.objects.filter(user=request.user, status='pending').exists()
    if pending:
        return Response(
            {'error': 'You already have a pending coin request'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    serializer = CoinRequestCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    coin_request = CoinRequest.objects.create(
        user=request.user,
        amount=serializer.validated_data.get('amount', 1000),
        reason=serializer.validated_data.get('reason', '')
    )
    
    return Response(CoinRequestSerializer(coin_request).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_coin_requests(request):
    """Get user's coin requests"""
    requests = CoinRequest.objects.filter(user=request.user)
    return Response(CoinRequestSerializer(requests, many=True).data)


# Admin coin request management
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_pending_requests(request):
    """Get all pending coin requests (admin only)"""
    requests = CoinRequest.objects.filter(status='pending')
    return Response(CoinRequestSerializer(requests, many=True).data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_approve_request(request, request_id):
    """Approve a coin request (admin only)"""
    try:
        coin_request = CoinRequest.objects.get(id=request_id, status='pending')
    except CoinRequest.DoesNotExist:
        return Response({'error': 'Request not found'}, status=status.HTTP_404_NOT_FOUND)
    
    coin_request.status = 'approved'
    coin_request.reviewed_by = request.user
    coin_request.reviewed_at = timezone.now()
    coin_request.save()
    
    # Add coins to user
    profile = coin_request.user.profile
    profile.coins += coin_request.amount
    profile.save()
    
    return Response(CoinRequestSerializer(coin_request).data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_deny_request(request, request_id):
    """Deny a coin request (admin only)"""
    try:
        coin_request = CoinRequest.objects.get(id=request_id, status='pending')
    except CoinRequest.DoesNotExist:
        return Response({'error': 'Request not found'}, status=status.HTTP_404_NOT_FOUND)
    
    coin_request.status = 'denied'
    coin_request.reviewed_by = request.user
    coin_request.reviewed_at = timezone.now()
    coin_request.save()
    
    return Response(CoinRequestSerializer(coin_request).data)


# Helper function to process game result
def process_game_result(user, game_type, bet_amount, won, payout, details):
    """Update user profile and create game history"""
    profile = user.profile
    
    # Check sufficient balance
    if profile.coins < bet_amount:
        return None, "Insufficient coins"
    
    # Deduct bet
    profile.coins -= bet_amount
    profile.total_wagered += bet_amount
    profile.games_played += 1
    
    # Process result
    if won:
        winnings = payout + bet_amount  # Return bet + winnings
        profile.coins += winnings
        profile.total_won += payout
    else:
        profile.total_lost += bet_amount
    
    profile.save()
    
    # Record history
    GameHistory.objects.create(
        user=user,
        game_type=game_type,
        bet_amount=bet_amount,
        won=won,
        payout=payout if won else -bet_amount,
        details=details
    )
    
    return profile, None


# Game Views
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def play_blackjack(request):
    """Play blackjack"""
    serializer = BlackjackActionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    action = serializer.validated_data['action']
    bet = serializer.validated_data['bet']
    game_state = serializer.validated_data.get('game_state')
    
    profile = request.user.profile
    
    # Check balance for new game
    if action == 'deal' and profile.coins < bet:
        return Response({'error': 'Insufficient coins'}, status=status.HTTP_400_BAD_REQUEST)
    
    game = BlackjackGame()
    result = game.play(bet, action, game_state)
    
    # Process completed game
    if result['status'] in ['win', 'lose', 'bust', 'blackjack', 'push']:
        won = result['status'] in ['win', 'blackjack']
        payout = result['payout']
        
        profile, error = process_game_result(
            request.user, 'blackjack', bet, won, 
            payout if won else 0, 
            {'player_hand': result['player_hand'], 'dealer_hand': result['dealer_hand']}
        )
        
        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
        
        result['coins'] = profile.coins
        result['is_bankrupt'] = profile.is_bankrupt()
    
    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def play_poker(request):
    """Play video poker"""
    serializer = PokerActionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    action = serializer.validated_data['action']
    bet = serializer.validated_data['bet']
    hold_indices = serializer.validated_data.get('hold_indices', [])
    game_state = serializer.validated_data.get('game_state')
    
    profile = request.user.profile
    
    if action == 'deal' and profile.coins < bet:
        return Response({'error': 'Insufficient coins'}, status=status.HTTP_400_BAD_REQUEST)
    
    game = PokerGame()
    
    if action == 'deal':
        result = game.deal()
    else:
        result = game.draw(game_state, hold_indices, bet)
        
        # Process completed game
        won = result['status'] == 'win'
        payout = result['payout']
        
        profile, error = process_game_result(
            request.user, 'poker', bet, won,
            payout if won else 0,
            {'hand': result['hand'], 'hand_type': result['hand_type']}
        )
        
        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
        
        result['coins'] = profile.coins
        result['is_bankrupt'] = profile.is_bankrupt()
    
    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def play_roulette(request):
    """Play roulette"""
    serializer = RouletteActionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    bet_type = serializer.validated_data['bet_type']
    bet_value = serializer.validated_data['bet_value']
    bet = serializer.validated_data['bet']
    
    profile = request.user.profile
    
    if profile.coins < bet:
        return Response({'error': 'Insufficient coins'}, status=status.HTTP_400_BAD_REQUEST)
    
    game = RouletteGame()
    result = game.spin(bet_type, bet_value, bet)
    
    won = result['won']
    payout = result['payout']
    
    profile, error = process_game_result(
        request.user, 'roulette', bet, won,
        payout if won else 0,
        {'result': result['result'], 'bet_type': bet_type, 'bet_value': bet_value}
    )
    
    if error:
        return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
    
    result['coins'] = profile.coins
    result['is_bankrupt'] = profile.is_bankrupt()
    
    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def play_dice(request):
    """Play dice"""
    serializer = DiceActionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    bet_type = serializer.validated_data['bet_type']
    bet_value = serializer.validated_data['bet_value']
    bet = serializer.validated_data['bet']
    
    profile = request.user.profile
    
    if profile.coins < bet:
        return Response({'error': 'Insufficient coins'}, status=status.HTTP_400_BAD_REQUEST)
    
    game = DiceGame()
    result = game.roll(bet_type, bet_value, bet)
    
    won = result['won']
    payout = result['payout']
    
    profile, error = process_game_result(
        request.user, 'dice', bet, won,
        payout if won else 0,
        {'die1': result['die1'], 'die2': result['die2'], 'total': result['total']}
    )
    
    if error:
        return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
    
    result['coins'] = profile.coins
    result['is_bankrupt'] = profile.is_bankrupt()
    
    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def play_minesweeper(request):
    """Play minesweeper"""
    serializer = MinesweeperActionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    action = serializer.validated_data['action']
    bet = serializer.validated_data['bet']
    game_state = serializer.validated_data.get('game_state')
    
    profile = request.user.profile
    
    game = MinesweeperGame()
    
    if action == 'create':
        if profile.coins < bet:
            return Response({'error': 'Insufficient coins'}, status=status.HTTP_400_BAD_REQUEST)
        
        grid_size = serializer.validated_data.get('grid_size', 5)
        num_mines = serializer.validated_data.get('num_mines', 5)
        result = game.create_game(grid_size, num_mines)
        
    elif action == 'reveal':
        tile_index = serializer.validated_data.get('tile_index')
        if tile_index is None:
            return Response({'error': 'tile_index required'}, status=status.HTTP_400_BAD_REQUEST)
        
        result = game.reveal_tile(game_state, tile_index, bet)
        
        # Process if game ended
        if result['status'] == 'lose':
            profile, error = process_game_result(
                request.user, 'minesweeper', bet, False, 0,
                {'revealed': result['revealed'], 'hit_mine': result.get('hit_mine')}
            )
            if error:
                return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
            result['coins'] = profile.coins
            result['is_bankrupt'] = profile.is_bankrupt()
            
    elif action == 'cashout':
        result = game.cashout(game_state, bet)
        
        payout = result['payout']
        profile, error = process_game_result(
            request.user, 'minesweeper', bet, True, payout,
            {'revealed': result['revealed'], 'multiplier': result['multiplier']}
        )
        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
        result['coins'] = profile.coins
        result['is_bankrupt'] = profile.is_bankrupt()
    
    return Response(result)


# Educational content about gambling
@api_view(['GET'])
@permission_classes([AllowAny])
def gambling_education(request):
    """Return educational content about gambling and house edge"""
    return Response({
        'title': 'Why You Can Never Win Against the House',
        'sections': [
            {
                'title': 'The House Edge Explained',
                'content': '''The house edge is a mathematical advantage that ensures casinos 
                always profit in the long run. Even if individual players win, the casino 
                always comes out ahead over time. In our games, we've implemented a 5-10% 
                house edge, which is typical of real casinos.'''
            },
            {
                'title': 'The Math Behind Your Losses',
                'content': '''Consider a simple coin flip game where you should win 50% of 
                the time. With a 7% house edge, your actual win rate drops to 43%. Over 
                100 bets of $10 each, you'd expect to lose about $70. The more you play, 
                the more certain your losses become.'''
            },
            {
                'title': 'Expected Value (EV)',
                'content': '''Every bet has an Expected Value - the average amount you'll 
                win or lose per bet over time. With a house edge, the EV is always negative 
                for the player. For example, a $10 bet with 7% house edge has an EV of 
                -$0.70. You're mathematically guaranteed to lose money over time.'''
            },
            {
                'title': 'The Gambler\'s Fallacy',
                'content': '''Many believe that after a losing streak, they're "due" for a 
                win. This is false. Each bet is independent - previous results don't 
                affect future outcomes. The dice don't remember, and neither do the cards.'''
            },
            {
                'title': 'Why Gambling is Harmful',
                'content': '''Beyond financial losses, gambling can lead to addiction, 
                relationship problems, depression, and anxiety. The rush of occasional 
                wins creates a psychological trap that keeps people playing despite 
                consistent losses. If you or someone you know struggles with gambling, 
                please seek help.'''
            },
            {
                'title': 'Resources for Help',
                'content': '''
                • National Problem Gambling Helpline: 1-800-522-4700
                • Gamblers Anonymous: www.gamblersanonymous.org
                • National Council on Problem Gambling: www.ncpgambling.org
                '''
            }
        ],
        'math_breakdown': {
            'blackjack': {
                'base_house_edge': '0.5%',
                'our_house_edge': '7%',
                'expected_loss_per_100_bets': '7%'
            },
            'roulette': {
                'base_house_edge': '5.26%',
                'our_house_edge': '11%',
                'expected_loss_per_100_bets': '11%'
            },
            'dice': {
                'base_house_edge': 'varies',
                'our_house_edge': '7%',
                'expected_loss_per_100_bets': '7%'
            },
            'poker': {
                'base_house_edge': '~3%',
                'our_house_edge': '8%',
                'expected_loss_per_100_bets': '8%'
            },
            'minesweeper': {
                'base_house_edge': '~2%',
                'our_house_edge': '8%',
                'expected_loss_per_100_bets': '8%'
            }
        }
    })
