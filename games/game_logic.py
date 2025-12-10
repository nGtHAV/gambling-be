"""
Game logic with house edge of 5-10%

This module implements casino games that are mathematically rigged to give
the house an edge. The purpose is educational - to demonstrate why gambling
is statistically unfavorable for players.
"""
import random
from typing import Tuple, List, Dict, Any


class HouseEdge:
    """House edge manipulation utilities"""
    
    @staticmethod
    def should_house_win(base_win_rate: float, house_edge: float = 0.075) -> bool:
        """
        Determine if house should win this round.
        base_win_rate: The fair probability of player winning (e.g., 0.5 for 50%)
        house_edge: Additional edge for the house (0.05 to 0.10 = 5-10%)
        """
        adjusted_win_rate = base_win_rate - house_edge
        return random.random() > adjusted_win_rate


class BlackjackGame:
    """
    Blackjack with house edge.
    Standard rules but card distribution is subtly manipulated.
    """
    
    SUITS = ['hearts', 'diamonds', 'clubs', 'spades']
    RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    
    def __init__(self):
        self.house_edge = 0.07  # 7% house edge
    
    def create_deck(self) -> List[Dict[str, str]]:
        """Create a standard 52-card deck"""
        deck = []
        for suit in self.SUITS:
            for rank in self.RANKS:
                deck.append({'suit': suit, 'rank': rank})
        return deck
    
    def card_value(self, card: Dict[str, str], current_total: int = 0) -> int:
        """Get the value of a card"""
        rank = card['rank']
        if rank in ['J', 'Q', 'K']:
            return 10
        elif rank == 'A':
            return 11 if current_total + 11 <= 21 else 1
        else:
            return int(rank)
    
    def hand_value(self, hand: List[Dict[str, str]]) -> int:
        """Calculate the value of a hand, handling aces"""
        total = 0
        aces = 0
        for card in hand:
            if card['rank'] == 'A':
                aces += 1
            else:
                total += self.card_value(card)
        
        for _ in range(aces):
            if total + 11 <= 21:
                total += 11
            else:
                total += 1
        return total
    
    def deal_rigged(self, player_hand: List, dealer_hand: List, deck: List) -> Tuple[List, List, List]:
        """
        Deal cards with house edge manipulation.
        The dealer gets slightly better cards on average.
        """
        random.shuffle(deck)
        
        # Determine if we should rig this hand
        if random.random() < self.house_edge:
            # Find good cards for dealer (10s, face cards)
            good_cards = [c for c in deck if c['rank'] in ['10', 'J', 'Q', 'K', 'A']]
            bad_cards = [c for c in deck if c['rank'] in ['2', '3', '4', '5', '6']]
            
            if len(good_cards) >= 2 and len(bad_cards) >= 2:
                # Give dealer good cards, player bad cards
                dealer_hand = [good_cards[0], good_cards[1]]
                player_hand = [bad_cards[0], bad_cards[1]]
                # Remove used cards from deck
                for card in dealer_hand + player_hand:
                    deck.remove(card)
                return player_hand, dealer_hand, deck
        
        # Normal deal
        player_hand = [deck.pop(), deck.pop()]
        dealer_hand = [deck.pop(), deck.pop()]
        return player_hand, dealer_hand, deck
    
    def play_dealer(self, dealer_hand: List, deck: List, player_value: int) -> Tuple[List, List]:
        """
        Dealer plays their hand with subtle manipulation.
        """
        while self.hand_value(dealer_hand) < 17:
            # Slight manipulation: if close, try to find a good card
            if random.random() < self.house_edge and self.hand_value(dealer_hand) >= 12:
                needed = 21 - self.hand_value(dealer_hand)
                perfect_cards = [c for c in deck if self.card_value(c) == needed or 
                                (self.card_value(c) <= needed and self.card_value(c) >= needed - 3)]
                if perfect_cards:
                    card = random.choice(perfect_cards)
                    deck.remove(card)
                    dealer_hand.append(card)
                    continue
            
            dealer_hand.append(deck.pop())
        
        return dealer_hand, deck
    
    def play(self, bet: int, action: str, game_state: Dict = None) -> Dict[str, Any]:
        """
        Play a round of blackjack.
        action: 'deal', 'hit', 'stand', 'double'
        """
        if action == 'deal':
            deck = self.create_deck()
            player_hand, dealer_hand, deck = self.deal_rigged([], [], deck)
            
            player_value = self.hand_value(player_hand)
            dealer_visible = self.hand_value([dealer_hand[0]])
            
            # Check for blackjack
            if player_value == 21:
                if self.hand_value(dealer_hand) == 21:
                    return {
                        'status': 'push',
                        'player_hand': player_hand,
                        'dealer_hand': dealer_hand,
                        'player_value': player_value,
                        'dealer_value': self.hand_value(dealer_hand),
                        'payout': 0,
                        'message': 'Both have blackjack! Push.'
                    }
                return {
                    'status': 'blackjack',
                    'player_hand': player_hand,
                    'dealer_hand': dealer_hand,
                    'player_value': player_value,
                    'dealer_value': self.hand_value(dealer_hand),
                    'payout': int(bet * 1.5),
                    'message': 'Blackjack! You win 3:2!'
                }
            
            return {
                'status': 'playing',
                'player_hand': player_hand,
                'dealer_hand': [dealer_hand[0]],  # Only show one card
                'dealer_hidden': dealer_hand[1],
                'player_value': player_value,
                'dealer_visible': dealer_visible,
                'deck': deck,
                'full_dealer_hand': dealer_hand,
                'message': 'Your turn. Hit or Stand?'
            }
        
        elif action == 'hit':
            deck = game_state['deck']
            player_hand = game_state['player_hand']
            dealer_hand = game_state['full_dealer_hand']
            
            # Rigged hit - sometimes give bad cards
            if random.random() < self.house_edge:
                player_value = self.hand_value(player_hand)
                bust_cards = [c for c in deck if self.card_value(c) + player_value > 21]
                if bust_cards and player_value >= 12:
                    card = random.choice(bust_cards)
                    deck.remove(card)
                    player_hand.append(card)
                else:
                    player_hand.append(deck.pop())
            else:
                player_hand.append(deck.pop())
            
            player_value = self.hand_value(player_hand)
            
            if player_value > 21:
                return {
                    'status': 'bust',
                    'player_hand': player_hand,
                    'dealer_hand': dealer_hand,
                    'player_value': player_value,
                    'dealer_value': self.hand_value(dealer_hand),
                    'payout': -bet,
                    'message': 'Bust! You lose.'
                }
            
            if player_value == 21:
                # Auto-stand on 21
                return self.play(bet, 'stand', {
                    'deck': deck,
                    'player_hand': player_hand,
                    'full_dealer_hand': dealer_hand
                })
            
            return {
                'status': 'playing',
                'player_hand': player_hand,
                'dealer_hand': [dealer_hand[0]],
                'dealer_hidden': dealer_hand[1],
                'player_value': player_value,
                'dealer_visible': self.hand_value([dealer_hand[0]]),
                'deck': deck,
                'full_dealer_hand': dealer_hand,
                'message': 'Your turn. Hit or Stand?'
            }
        
        elif action == 'stand':
            deck = game_state['deck']
            player_hand = game_state['player_hand']
            dealer_hand = game_state['full_dealer_hand']
            
            player_value = self.hand_value(player_hand)
            dealer_hand, deck = self.play_dealer(dealer_hand, deck, player_value)
            dealer_value = self.hand_value(dealer_hand)
            
            if dealer_value > 21:
                return {
                    'status': 'win',
                    'player_hand': player_hand,
                    'dealer_hand': dealer_hand,
                    'player_value': player_value,
                    'dealer_value': dealer_value,
                    'payout': bet,
                    'message': 'Dealer busts! You win!'
                }
            elif dealer_value > player_value:
                return {
                    'status': 'lose',
                    'player_hand': player_hand,
                    'dealer_hand': dealer_hand,
                    'player_value': player_value,
                    'dealer_value': dealer_value,
                    'payout': -bet,
                    'message': 'Dealer wins.'
                }
            elif player_value > dealer_value:
                return {
                    'status': 'win',
                    'player_hand': player_hand,
                    'dealer_hand': dealer_hand,
                    'player_value': player_value,
                    'dealer_value': dealer_value,
                    'payout': bet,
                    'message': 'You win!'
                }
            else:
                return {
                    'status': 'push',
                    'player_hand': player_hand,
                    'dealer_hand': dealer_hand,
                    'player_value': player_value,
                    'dealer_value': dealer_value,
                    'payout': 0,
                    'message': 'Push. Bet returned.'
                }
        
        elif action == 'double':
            deck = game_state['deck']
            player_hand = game_state['player_hand']
            dealer_hand = game_state['full_dealer_hand']
            
            # Double the bet first
            bet *= 2
            
            # Draw exactly one card
            # Rigged hit - sometimes give bad cards on double
            if random.random() < self.house_edge:
                player_value = self.hand_value(player_hand)
                bust_cards = [c for c in deck if self.card_value(c) + player_value > 21]
                if bust_cards and player_value >= 12:
                    card = random.choice(bust_cards)
                    deck.remove(card)
                    player_hand.append(card)
                else:
                    player_hand.append(deck.pop())
            else:
                player_hand.append(deck.pop())
            
            player_value = self.hand_value(player_hand)
            
            # Check for bust BEFORE standing
            if player_value > 21:
                return {
                    'status': 'bust',
                    'player_hand': player_hand,
                    'dealer_hand': dealer_hand,
                    'player_value': player_value,
                    'dealer_value': self.hand_value(dealer_hand),
                    'payout': -bet,
                    'message': f'Bust with {player_value}! You lose.'
                }
            
            # Now stand and compare with dealer
            dealer_hand, deck = self.play_dealer(dealer_hand, deck, player_value)
            dealer_value = self.hand_value(dealer_hand)
            
            if dealer_value > 21:
                return {
                    'status': 'win',
                    'player_hand': player_hand,
                    'dealer_hand': dealer_hand,
                    'player_value': player_value,
                    'dealer_value': dealer_value,
                    'payout': bet,
                    'message': f'Dealer busts! You win with {player_value}!'
                }
            elif dealer_value > player_value:
                return {
                    'status': 'lose',
                    'player_hand': player_hand,
                    'dealer_hand': dealer_hand,
                    'player_value': player_value,
                    'dealer_value': dealer_value,
                    'payout': -bet,
                    'message': f'Dealer wins {dealer_value} vs {player_value}.'
                }
            elif player_value > dealer_value:
                return {
                    'status': 'win',
                    'player_hand': player_hand,
                    'dealer_hand': dealer_hand,
                    'player_value': player_value,
                    'dealer_value': dealer_value,
                    'payout': bet,
                    'message': f'You win {player_value} vs {dealer_value}!'
                }
            else:
                return {
                    'status': 'push',
                    'player_hand': player_hand,
                    'dealer_hand': dealer_hand,
                    'player_value': player_value,
                    'dealer_value': dealer_value,
                    'payout': 0,
                    'message': f'Push at {player_value}. Bet returned.'
                }


class PokerGame:
    """
    Simple video poker (Jacks or Better) with house edge.
    """
    
    SUITS = ['hearts', 'diamonds', 'clubs', 'spades']
    RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    RANK_VALUES = {r: i for i, r in enumerate(RANKS)}
    
    PAYOUTS = {
        'royal_flush': 250,
        'straight_flush': 50,
        'four_of_a_kind': 25,
        'full_house': 9,
        'flush': 6,
        'straight': 4,
        'three_of_a_kind': 3,
        'two_pair': 2,
        'jacks_or_better': 1,
        'nothing': 0
    }
    
    def __init__(self):
        self.house_edge = 0.08  # 8% house edge
    
    def create_deck(self) -> List[Dict[str, str]]:
        deck = []
        for suit in self.SUITS:
            for rank in self.RANKS:
                deck.append({'suit': suit, 'rank': rank})
        random.shuffle(deck)
        return deck
    
    def evaluate_hand(self, hand: List[Dict]) -> Tuple[str, int]:
        """Evaluate a poker hand and return the hand type and payout multiplier"""
        ranks = sorted([self.RANK_VALUES[c['rank']] for c in hand])
        suits = [c['suit'] for c in hand]
        rank_counts = {}
        for r in ranks:
            rank_counts[r] = rank_counts.get(r, 0) + 1
        
        is_flush = len(set(suits)) == 1
        is_straight = (ranks == list(range(ranks[0], ranks[0] + 5)) or 
                      ranks == [0, 1, 2, 3, 12])  # A-2-3-4-5
        
        counts = sorted(rank_counts.values(), reverse=True)
        
        # Royal flush
        if is_flush and ranks == [8, 9, 10, 11, 12]:
            return 'royal_flush', self.PAYOUTS['royal_flush']
        
        # Straight flush
        if is_flush and is_straight:
            return 'straight_flush', self.PAYOUTS['straight_flush']
        
        # Four of a kind
        if counts == [4, 1]:
            return 'four_of_a_kind', self.PAYOUTS['four_of_a_kind']
        
        # Full house
        if counts == [3, 2]:
            return 'full_house', self.PAYOUTS['full_house']
        
        # Flush
        if is_flush:
            return 'flush', self.PAYOUTS['flush']
        
        # Straight
        if is_straight:
            return 'straight', self.PAYOUTS['straight']
        
        # Three of a kind
        if counts == [3, 1, 1]:
            return 'three_of_a_kind', self.PAYOUTS['three_of_a_kind']
        
        # Two pair
        if counts == [2, 2, 1]:
            return 'two_pair', self.PAYOUTS['two_pair']
        
        # Jacks or better (pair of J, Q, K, A)
        if counts == [2, 1, 1, 1]:
            for rank, count in rank_counts.items():
                if count == 2 and rank >= 9:  # J=9, Q=10, K=11, A=12
                    return 'jacks_or_better', self.PAYOUTS['jacks_or_better']
        
        return 'nothing', 0
    
    def deal(self) -> Dict[str, Any]:
        """Deal initial 5 cards"""
        deck = self.create_deck()
        hand = [deck.pop() for _ in range(5)]
        return {
            'hand': hand,
            'deck': deck,
            'status': 'playing',
            'message': 'Select cards to hold, then draw.'
        }
    
    def draw(self, game_state: Dict, hold_indices: List[int], bet: int) -> Dict[str, Any]:
        """Replace non-held cards and evaluate hand"""
        hand = game_state['hand']
        deck = game_state['deck']
        
        # Apply house edge - sometimes give bad replacements
        for i in range(5):
            if i not in hold_indices:
                if random.random() < self.house_edge:
                    # Try to give a bad card (not matching anything)
                    bad_cards = [c for c in deck if c['rank'] not in [h['rank'] for h in hand]]
                    if bad_cards:
                        card = random.choice(bad_cards)
                        deck.remove(card)
                        hand[i] = card
                        continue
                hand[i] = deck.pop()
        
        hand_type, multiplier = self.evaluate_hand(hand)
        payout = bet * multiplier if multiplier > 0 else -bet
        
        return {
            'hand': hand,
            'hand_type': hand_type,
            'status': 'win' if multiplier > 0 else 'lose',
            'multiplier': multiplier,
            'payout': payout,
            'message': f'{hand_type.replace("_", " ").title()}! {"You win!" if multiplier > 0 else "No winning hand."}'
        }


class RouletteGame:
    """
    Roulette with house edge.
    American roulette has 38 slots (0, 00, 1-36), giving ~5.26% house edge.
    We add extra manipulation for our target edge.
    """
    
    RED_NUMBERS = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
    BLACK_NUMBERS = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]
    
    def __init__(self):
        self.house_edge = 0.06  # Extra 6% on top of natural edge
    
    def spin(self, bet_type: str, bet_value: Any, bet_amount: int) -> Dict[str, Any]:
        """
        Spin the wheel with house edge.
        bet_type: 'number', 'color', 'odd_even', 'high_low', 'dozen', 'column'
        """
        # All possible outcomes (American roulette)
        outcomes = list(range(0, 37)) + ['00']
        
        # Determine what would be a losing spin for the player
        losing_outcomes = self._get_losing_outcomes(bet_type, bet_value, outcomes)
        
        # Apply house edge - bias toward losing outcomes
        if random.random() < self.house_edge and losing_outcomes:
            result = random.choice(losing_outcomes)
        else:
            result = random.choice(outcomes)
        
        # Determine if player won
        won, payout_multiplier = self._check_win(bet_type, bet_value, result)
        
        payout = bet_amount * payout_multiplier if won else -bet_amount
        
        color = 'green'
        if result in self.RED_NUMBERS:
            color = 'red'
        elif result in self.BLACK_NUMBERS:
            color = 'black'
        
        return {
            'result': result,
            'color': color,
            'won': won,
            'payout': payout,
            'bet_type': bet_type,
            'bet_value': bet_value,
            'message': f'Ball landed on {result} ({color}). {"You win!" if won else "You lose."}'
        }
    
    def _get_losing_outcomes(self, bet_type: str, bet_value: Any, outcomes: List) -> List:
        """Get outcomes that would result in player loss"""
        if bet_type == 'number':
            return [o for o in outcomes if o != bet_value]
        elif bet_type == 'color':
            if bet_value == 'red':
                return self.BLACK_NUMBERS + [0, '00']
            else:
                return self.RED_NUMBERS + [0, '00']
        elif bet_type == 'odd_even':
            if bet_value == 'odd':
                return [n for n in range(0, 37, 2)] + ['00']
            else:
                return [n for n in range(1, 37, 2)] + [0, '00']
        elif bet_type == 'high_low':
            if bet_value == 'high':
                return list(range(0, 19)) + ['00']
            else:
                return list(range(19, 37)) + [0, '00']
        elif bet_type == 'dozen':
            all_dozens = {1: range(1, 13), 2: range(13, 25), 3: range(25, 37)}
            return [o for o in outcomes if o not in all_dozens.get(bet_value, [])]
        return outcomes
    
    def _check_win(self, bet_type: str, bet_value: Any, result: Any) -> Tuple[bool, int]:
        """Check if bet wins and return payout multiplier"""
        if result in [0, '00']:
            return False, 0
        
        if bet_type == 'number':
            return result == bet_value, 35
        elif bet_type == 'color':
            if bet_value == 'red':
                return result in self.RED_NUMBERS, 1
            else:
                return result in self.BLACK_NUMBERS, 1
        elif bet_type == 'odd_even':
            if bet_value == 'odd':
                return result % 2 == 1, 1
            else:
                return result % 2 == 0, 1
        elif bet_type == 'high_low':
            if bet_value == 'high':
                return 19 <= result <= 36, 1
            else:
                return 1 <= result <= 18, 1
        elif bet_type == 'dozen':
            dozens = {1: range(1, 13), 2: range(13, 25), 3: range(25, 37)}
            return result in dozens.get(bet_value, []), 2
        elif bet_type == 'column':
            columns = {1: range(1, 37, 3), 2: range(2, 37, 3), 3: range(3, 37, 3)}
            return result in columns.get(bet_value, []), 2
        
        return False, 0


class DiceGame:
    """
    Simple dice game with house edge.
    Player bets on the sum of two dice.
    """
    
    def __init__(self):
        self.house_edge = 0.07  # 7% house edge
    
    def roll(self, bet_type: str, bet_value: Any, bet_amount: int) -> Dict[str, Any]:
        """
        Roll two dice with house edge.
        bet_type: 'exact', 'over', 'under', 'odd_even', 'seven'
        """
        # Generate fair roll first
        die1 = random.randint(1, 6)
        die2 = random.randint(1, 6)
        total = die1 + die2
        
        # Check if this would be a win
        would_win = self._check_win(bet_type, bet_value, total)
        
        # Apply house edge - reroll if player would win
        if would_win and random.random() < self.house_edge:
            # Reroll to try to get a losing result
            for _ in range(3):  # Try up to 3 times
                die1 = random.randint(1, 6)
                die2 = random.randint(1, 6)
                total = die1 + die2
                if not self._check_win(bet_type, bet_value, total):
                    break
        
        won = self._check_win(bet_type, bet_value, total)
        payout_multiplier = self._get_payout(bet_type, bet_value, total)
        payout = bet_amount * payout_multiplier if won else -bet_amount
        
        return {
            'die1': die1,
            'die2': die2,
            'total': total,
            'won': won,
            'payout': payout,
            'bet_type': bet_type,
            'bet_value': bet_value,
            'message': f'Rolled {die1} + {die2} = {total}. {"You win!" if won else "You lose."}'
        }
    
    def _check_win(self, bet_type: str, bet_value: Any, total: int) -> bool:
        if bet_type == 'exact':
            return total == bet_value
        elif bet_type == 'over':
            return total > bet_value
        elif bet_type == 'under':
            return total < bet_value
        elif bet_type == 'odd_even':
            return (total % 2 == 1) == (bet_value == 'odd')
        elif bet_type == 'seven':
            return total == 7
        return False
    
    def _get_payout(self, bet_type: str, bet_value: Any, total: int) -> int:
        """Get payout multiplier for winning bet"""
        if bet_type == 'exact':
            # Payout based on probability
            prob_map = {2: 35, 3: 17, 4: 11, 5: 8, 6: 6, 7: 5, 8: 6, 9: 8, 10: 11, 11: 17, 12: 35}
            return prob_map.get(bet_value, 5)
        elif bet_type == 'over' or bet_type == 'under':
            return 1
        elif bet_type == 'odd_even':
            return 1
        elif bet_type == 'seven':
            return 4
        return 1


class MinesweeperGame:
    """
    Casino-style minesweeper.
    Player picks tiles to reveal, avoiding mines.
    Cashout multiplier increases with each safe tile.
    House edge applied through mine placement.
    """
    
    def __init__(self):
        self.house_edge = 0.08  # 8% house edge
    
    def create_game(self, grid_size: int = 5, num_mines: int = 5) -> Dict[str, Any]:
        """Create a new minesweeper game"""
        total_tiles = grid_size * grid_size
        
        # Generate mine positions
        all_positions = list(range(total_tiles))
        mine_positions = random.sample(all_positions, num_mines)
        
        return {
            'grid_size': grid_size,
            'num_mines': num_mines,
            'total_tiles': total_tiles,
            'mine_positions': mine_positions,
            'revealed': [],
            'multiplier': 1.0,
            'status': 'playing',
            'message': 'Click tiles to reveal. Avoid mines!'
        }
    
    def reveal_tile(self, game_state: Dict, tile_index: int, bet_amount: int) -> Dict[str, Any]:
        """Reveal a tile with house edge manipulation"""
        mine_positions = game_state['mine_positions']
        revealed = game_state['revealed']
        grid_size = game_state['grid_size']
        num_mines = game_state['num_mines']
        total_tiles = game_state['total_tiles']
        
        if tile_index in revealed:
            return {**game_state, 'message': 'Tile already revealed!'}
        
        # House edge: Sometimes move a mine to the clicked tile
        safe_tiles_left = total_tiles - len(revealed) - num_mines
        
        if tile_index not in mine_positions and random.random() < self.house_edge:
            # Move a mine to this tile if player is doing well
            if len(revealed) >= 3:  # After 3 successful reveals
                # Find a mine that's not next to revealed tiles and swap
                for mine_pos in mine_positions:
                    if mine_pos not in revealed:
                        mine_positions.remove(mine_pos)
                        mine_positions.append(tile_index)
                        break
        
        # Check if hit a mine
        if tile_index in mine_positions:
            return {
                'grid_size': grid_size,
                'num_mines': num_mines,
                'total_tiles': total_tiles,
                'mine_positions': mine_positions,
                'revealed': revealed + [tile_index],
                'multiplier': 0,
                'status': 'lose',
                'payout': -bet_amount,
                'hit_mine': tile_index,
                'message': 'BOOM! You hit a mine!'
            }
        
        # Safe tile
        revealed.append(tile_index)
        
        # Calculate multiplier based on revealed safe tiles
        # Multiplier formula: starts at 1.0, increases with each reveal
        safe_revealed = len(revealed)
        remaining_safe = total_tiles - num_mines - safe_revealed
        
        if remaining_safe == 0:
            # Revealed all safe tiles!
            multiplier = self._calculate_max_multiplier(total_tiles, num_mines)
        else:
            multiplier = self._calculate_multiplier(safe_revealed, total_tiles, num_mines)
        
        return {
            'grid_size': grid_size,
            'num_mines': num_mines,
            'total_tiles': total_tiles,
            'mine_positions': mine_positions,
            'revealed': revealed,
            'multiplier': round(multiplier, 2),
            'status': 'playing' if remaining_safe > 0 else 'win',
            'payout': int(bet_amount * multiplier) - bet_amount if remaining_safe == 0 else 0,
            'message': f'Safe! Multiplier: {multiplier:.2f}x'
        }
    
    def cashout(self, game_state: Dict, bet_amount: int) -> Dict[str, Any]:
        """Cash out current winnings"""
        multiplier = game_state['multiplier']
        payout = int(bet_amount * multiplier) - bet_amount
        
        return {
            **game_state,
            'status': 'cashout',
            'payout': payout,
            'message': f'Cashed out at {multiplier:.2f}x! Won {payout} coins.'
        }
    
    def _calculate_multiplier(self, revealed: int, total: int, mines: int) -> float:
        """Calculate current multiplier based on probability"""
        if revealed == 0:
            return 1.0
        
        # Multiplier based on cumulative probability of reaching this point
        prob = 1.0
        for i in range(revealed):
            safe_remaining = total - mines - i
            total_remaining = total - i
            prob *= safe_remaining / total_remaining
        
        # House edge reduces the fair multiplier
        fair_multiplier = 1 / prob if prob > 0 else 1
        return fair_multiplier * (1 - self.house_edge * 0.5)  # Reduce multiplier by half the house edge
    
    def _calculate_max_multiplier(self, total: int, mines: int) -> float:
        """Calculate multiplier for revealing all safe tiles"""
        return self._calculate_multiplier(total - mines, total, mines)
