import numpy as np
import random
import uuid
from typing import Dict, List, Tuple, Optional
from app.schemas.game_state import GameState, Card, Pile, MoveRequest

class SpiderSolitaire:
    # Constants from original game (UI-related removed)
    FACEDOWN = 15
    ROWBASE = 5
    HISTORY_SIZE = 1000
    INITIAL_DEALS = 5
    
    def __init__(self):
        self.initialize_game()
        
    def initialize_game(self):
        """Initialize game state matching original implementation"""
        self.cardsarray = np.zeros((80, 10, 2), dtype='int32')  # Main game board [row,col,(rank,suit)]
        self.facedown_cards = np.zeros((80, 10, 2), dtype='int32')  # Hidden card data
        self.card_ids = np.empty((80, 10), dtype='object')      # Card unique IDs
        self.lastcard = np.zeros(10, dtype='int32')             # Last card in each column
        self.histrec = [None] * self.HISTORY_SIZE               # Move history
        self.deck = np.zeros(104, dtype='int32')                # Initialize the deck (104 cards for spider solitaire - 2 decks)
        
        # Game state variables
        self.nextcard = 0               # Next card to deal
        self.historycount = 0           # Move counter
        self.dealnext10 = 0             # Number of deals completed
        self.difficulty = 9             # Default difficulty (0-9)
        self.completed_sequences = 0    # Count of completed suits removed
        
        # Game logic tracking (originally UI-related but needed for logic)
        self.removedsuit = np.zeros(9, dtype='int32')  # Removed suits tracking
    
    def new_game(self, difficulty: int = 9) -> GameState:
        """Start a new game with specified difficulty (0-9)"""
        self.initialize_game()
        self.difficulty = 9 - difficulty  # Invert difficulty to match original
        
        self.shuffle()
        self.setup_initial_deal()
        return self.get_game_state()
    
    def shuffle(self):
        """Shuffle the deck matching original game's logic"""
        # Initialize two decks (104 cards)
        for i in range(1, 105):
            self.deck[i-1] = ((i-1) % 52) + 1  # Values 1-52 repeated twice
        
        # Apply original game's special shuffling logic
        random.seed(78)  # Fixed seed for reproducibility as in original
        
        # Difficulty-based initial cards (first 8 cards must be unique ranks)
        newdig = np.zeros(14, dtype='int32')
        if self.difficulty < 9:
            unique_positions = random.sample(range(52), 8)
            for pos in unique_positions:
                rank = self.deck[pos] % 13 + 1
                while rank in newdig:
                    # Reshuffle until we get unique ranks
                    np.random.shuffle(self.deck[:52])
                    rank = self.deck[pos] % 13 + 1
                newdig[pos % 8] = rank
        
        # Apply original game's special card positioning
        temp = self.deck[44:56].copy()
        self.deck[44:56] = self.deck[12:24]
        self.deck[12:24] = temp
        self.deck[:12] = self.deck[44:56]
    
    def setup_initial_deal(self):
        """Deal initial cards matching original game's setup"""
        self.nextcard = 0
        for jl in range(10):
            # Initialize column lengths
            self.lastcard[jl] = self.ROWBASE + (5 if jl < 4 else 4)  # First 4 cols get 6 cards, others get 5
                
        # Deal initial cards - matches original 7-row deal
        rowdepth = self.ROWBASE
        while rowdepth < self.ROWBASE + 7:
            for jl in range(10):
                if self.nextcard < 44 or (self.nextcard < 54 and rowdepth == self.ROWBASE + 6):
                    # Deal facedown cards (first 44 cards, plus 10 more in last row)
                    self.cardsarray[rowdepth, jl, 0] = self.FACEDOWN
                    self.facedown_cards[rowdepth, jl, 0] = self.deck[self.nextcard] % 13 + 1
                    self.facedown_cards[rowdepth, jl, 1] = self.deck[self.nextcard] % 4 + 1
                    self.card_ids[rowdepth, jl] = str(uuid.uuid4())
                    self.nextcard += 1
                elif self.nextcard < 54:
                    # Deal faceup cards (positions 44-53)
                    self.cardsarray[rowdepth, jl, 0] = self.deck[self.nextcard] % 13 + 1
                    self.cardsarray[rowdepth, jl, 1] = self.deck[self.nextcard] % 4 + 1
                    self.card_ids[rowdepth, jl] = str(uuid.uuid4())
                    self.nextcard += 1
            rowdepth += 1
    
    def check_sequence_length(self, row: int, col: int) -> int:
        """Check how many cards are in sequence from this position"""
        length = 1
        while (row + length <= self.lastcard[col] and
               self.cardsarray[row + length, col, 0] == self.cardsarray[row + length - 1, col, 0] - 1):
            length += 1
        return length
    
    def display_board(self):
        """Display the current game board in terminal with colored output"""
        # Define card symbols and colors
        suits_symbols = {1: '♥', 2: '♦', 3: '♣', 4: '♠'}
        suits_colors = {1: '\033[91m', 2: '\033[91m', 3: '\033[92m', 4: '\033[92m'}  # Red/Green
        reset_color = '\033[0m'
        facedown_symbol = '0'
        
        # Find how many rows we need to display
        max_height = max(self.lastcard) - self.ROWBASE + 1
        if max_height < 1:
            max_height = 1
        
        print("\n" + "="*80)
        print(f"Spider Solitaire (Difficulty: {9 - self.difficulty}, Completed: {self.completed_sequences})")
        print(f"Cards remaining: {104 - self.nextcard}, Deals left: {self.INITIAL_DEALS - self.dealnext10}")
        print("="*80)
        
        # Print column headers
        print("   " + "   ".join(f"Col {i}" for i in range(10)))
        
        for row in range(self.ROWBASE, self.ROWBASE + max_height):
            row_display = []
            for col in range(10):
                if row <= self.lastcard[col]:
                    if self.cardsarray[row, col, 0] == self.FACEDOWN:
                        # Facedown card
                        row_display.append(f"{facedown_symbol}")
                    else:
                        # Faceup card
                        rank = self.cardsarray[row, col, 0]
                        suit = self.cardsarray[row, col, 1]
                        
                        # Convert rank to letter for face cards
                        rank_str = str(rank)
                        
                        color = suits_colors.get(suit, '')
                        row_display.append(f"{color}{rank_str}{reset_color}")
                else:
                    row_display.append("  ")  # Empty space
                    
            # Print the row with column indicators
            print(f"{row-self.ROWBASE:2d} " + "  ".join(row_display))
        
        print("="*80 + "\n")
    
    def execute_move(self, request: MoveRequest) -> GameState:
        """Execute a valid move with original game's logic"""
        sequence_length = self.check_sequence_length(request.from_row, request.from_col)

        # Check if destination column is empty
        is_empty_column = (self.cardsarray[self.ROWBASE, request.to_col, 0] == 0)
        
        # Record move details
        move_details = {
            'type': 'move',
            'from_row': request.from_row,
            'from_col': request.from_col,
            'to_row': request.to_row,
            'to_col': request.to_col,
            'cards_moved': [],
            'revealed_card': None,
            'completed_sequence': None
        }
        
        # Check for facedown card reveal
        if (request.from_row > self.ROWBASE and 
            self.cardsarray[request.from_row - 1, request.from_col, 0] == self.FACEDOWN):
            move_details['revealed_card'] = {
                'row': request.from_row - 1,
                'col': request.from_col,
                'rank': self.facedown_cards[request.from_row - 1, request.from_col, 0],
                'suit': self.facedown_cards[request.from_row - 1, request.from_col, 1],
                'id': self.card_ids[request.from_row - 1, request.from_col]
            }
        
        # Perform the move
        for i in range(sequence_length):
            # Move card data
            src_row = request.from_row + i
            
            # Calculate destination row differently for empty columns
            if is_empty_column:
                dest_row = self.ROWBASE + i
            else:
                dest_row = request.to_row + 1 + i
            
            self.cardsarray[dest_row, request.to_col] = self.cardsarray[src_row, request.from_col]
            self.card_ids[dest_row, request.to_col] = self.card_ids[src_row, request.from_col]
            
            # Clear source position
            self.cardsarray[src_row, request.from_col] = 0
            self.card_ids[src_row, request.from_col] = None
            
            # Record moved card
            move_details['cards_moved'].append({
                'rank': self.cardsarray[dest_row, request.to_col, 0],
                'suit': self.cardsarray[dest_row, request.to_col, 1],
                'from_row': src_row,
                'from_col': request.from_col,
                'to_row': dest_row,
                'to_col': request.to_col,
                'id': self.card_ids[dest_row, request.to_col]
            })
        
        # Update last card positions
        if is_empty_column:
            self.lastcard[request.to_col] = self.ROWBASE + sequence_length - 1
        else:
            self.lastcard[request.to_col] = request.to_row + sequence_length
            
        self.lastcard[request.from_col] = request.from_row - 1
        
        # Reveal facedown card if needed
        if move_details.get('revealed_card'):
            rc = move_details['revealed_card']
            self.cardsarray[rc['row'], rc['col'], 0] = rc['rank']
            self.cardsarray[rc['row'], rc['col'], 1] = rc['suit']
            self.card_ids[rc['row'], rc['col']] = rc['id']
        
        # Check for completed sequences
        completed = self.check_completed_suits()
        if completed:
            move_details['completed_sequence'] = completed
        
        # Store move in history
        self.histrec[self.historycount % self.HISTORY_SIZE] = move_details
        self.historycount += 1
        
        return self.get_game_state()
    
    def check_completed_suits(self) -> Optional[Dict]:
        """Check for completed suits matching original game logic"""
        for col in range(10):
            if self.lastcard[col] - self.ROWBASE + 1 < 13:
                continue
                
            # Check for 13-card sequence of same suit
            top_row = self.lastcard[col] - 12
            suit = self.cardsarray[top_row, col, 1]
            is_complete = True
            
            for i in range(13):
                if (self.cardsarray[top_row + i, col, 0] != self.cardsarray[top_row, col, 0] - i or
                    self.cardsarray[top_row + i, col, 1] != suit):
                    is_complete = False
                    break
            
            if is_complete:
                # Remove the sequence
                for i in range(13):
                    self.cardsarray[top_row + i, col] = 0
                    self.card_ids[top_row + i, col] = None
                
                self.lastcard[col] = top_row - 1
                self.completed_sequences += 1
                
                # Track removed suit
                for i in range(9):
                    if self.removedsuit[i] == 0:
                        self.removedsuit[i] = suit
                        break
                
                # Return completion details
                return {
                    'column': col,
                    'suit': suit,
                    'top_rank': self.cardsarray[top_row, col, 0],
                    'cards': [(top_row + i, col) for i in range(13)]
                }
        return None
    
    def deal_cards(self) -> GameState:
        """Deal 10 more cards matching original game logic"""
        if self.dealnext10 >= self.INITIAL_DEALS:
            raise ValueError("No more cards to deal")
            
        # Record the deal in history
        move_details = {
            'type': 'deal',
            'cards_dealt': [],
            'lastcards_before': self.lastcard.copy()
        }
        
        for col in range(10):
            if self.nextcard >= 104:
                raise ValueError("No more cards in deck")
                
            target_row = self.lastcard[col] + 1
            rank = self.deck[self.nextcard] % 13 + 1
            suit = self.deck[self.nextcard] % 4 + 1
            
            self.cardsarray[target_row, col, 0] = rank
            self.cardsarray[target_row, col, 1] = suit
            self.card_ids[target_row, col] = str(uuid.uuid4())
            self.lastcard[col] = target_row
            
            move_details['cards_dealt'].append({
                'row': target_row,
                'col': col,
                'rank': rank,
                'suit': suit,
                'id': self.card_ids[target_row, col]
            })
            self.nextcard += 1
        
        # Store the deal in history
        self.histrec[self.historycount % self.HISTORY_SIZE] = move_details
        self.dealnext10 += 1
        self.historycount += 1
        
        return self.get_game_state()
    
    def auto_move(self, from_row: int, from_col: int) -> bool:
        """Implement original game's auto-move logic (cardfrontclick)"""
        if from_col < 0 or from_col > 9 or from_row < self.ROWBASE:
            return False
            
        if self.cardsarray[from_row, from_col, 0] == 0:
            return False
            
        # Find all possible destinations
        possible_moves = []
        card_rank = self.cardsarray[from_row, from_col, 0]
        card_suit = self.cardsarray[from_row, from_col, 1]
        sequence_length = self.check_sequence_length(from_row, from_col)
        
        for dest_col in range(10):
            if dest_col == from_col:
                continue
                
            if self.cardsarray[self.ROWBASE, dest_col, 0] == 0:
                # Empty column - must move entire sequence
                if from_row == self.ROWBASE or sequence_length == (self.lastcard[from_col] - from_row + 1):
                    possible_moves.append((self.ROWBASE, dest_col))
            else:
                # Non-empty column - check suit and rank
                dest_row = self.lastcard[dest_col]
                if (self.cardsarray[dest_row, dest_col, 0] == card_rank + 1):
                    possible_moves.append((dest_row, dest_col))
        
        # Implement original game's priority logic
        if possible_moves:
            # Prefer same-suit destinations
            same_suit_moves = [m for m in possible_moves if 
                              self.cardsarray[m[0], m[1], 1] == card_suit]
            if same_suit_moves:
                self.execute_move(MoveRequest(
                    from_row=from_row,
                    from_col=from_col,
                    to_row=same_suit_moves[0][0],
                    to_col=same_suit_moves[0][1]
                ))
                return True
            else:
                self.execute_move(MoveRequest(
                    from_row=from_row,
                    from_col=from_col,
                    to_row=possible_moves[0][0],
                    to_col=possible_moves[0][1]
                ))
                return True
        return False
    
    def solve(self) -> GameState:
        """Implement original game's solve logic (joinz)"""
        moved = True
        while moved:
            moved = False
            
            # Check for completed suits first
            if self.check_completed_suits():
                moved = True
                continue
                
            # Try to join sequences of same suit
            for from_col in range(10):
                if self.cardsarray[self.ROWBASE, from_col, 0] == 0:
                    continue
                    
                from_row = self.lastcard[from_col]
                card_rank = self.cardsarray[from_row, from_col, 0]
                card_suit = self.cardsarray[from_row, from_col, 1]
                
                # Look for matching sequences in other columns
                for to_col in range(10):
                    if from_col == to_col:
                        continue
                        
                    if self.cardsarray[self.ROWBASE, to_col, 0] == 0:
                        # Try moving to empty column
                        if self.auto_move(from_row, from_col):
                            moved = True
                            break
                    else:
                        # Try moving to matching sequence
                        to_row = self.lastcard[to_col]
                        if (self.cardsarray[to_row, to_col, 0] == card_rank + 1 and
                            self.cardsarray[to_row, to_col, 1] == card_suit):
                            if self.auto_move(from_row, from_col):
                                moved = True
                                break
                
                if moved:
                    break
            
            # If no moves found, deal more cards if possible
            if not moved and self.dealnext10 < self.INITIAL_DEALS:
                self.deal_cards()
                moved = True
        
        return self.get_game_state()
    
    def undo_move(self) -> GameState:
        """Undo the last move matching original game logic"""
        if self.historycount <= 0:
            raise ValueError("No moves to undo")
        
        # Get the last move (using circular buffer)
        hist_index = (self.historycount - 1) % self.HISTORY_SIZE
        move_details = self.histrec[hist_index]
        
        if move_details is None:
            raise ValueError("Invalid move history")
        
        if move_details['type'] == 'move':
            # Undo a card movement
            for card_data in reversed(move_details['cards_moved']):
                # Move cards back to original position
                self.cardsarray[card_data['from_row'], card_data['from_col'], 0] = card_data['rank']
                self.cardsarray[card_data['from_row'], card_data['from_col'], 1] = card_data['suit']
                self.card_ids[card_data['from_row'], card_data['from_col']] = card_data['id']
                
                # Clear destination position
                self.cardsarray[card_data['to_row'], card_data['to_col']] = 0
                self.card_ids[card_data['to_row'], card_data['to_col']] = None
            
            # Update last card positions
            self.lastcard[move_details['from_col']] = move_details['from_row'] + len(move_details['cards_moved']) - 1
            self.lastcard[move_details['to_col']] = move_details['to_row']
            
            # If a card was revealed, cover it back up
            if move_details.get('revealed_card'):
                rc = move_details['revealed_card']
                self.cardsarray[rc['row'], rc['col'], 0] = self.FACEDOWN
                self.facedown_cards[rc['row'], rc['col'], 0] = rc['rank']
                self.facedown_cards[rc['row'], rc['col'], 1] = rc['suit']
                self.card_ids[rc['row'], rc['col']] = rc['id']
            
            # If a sequence was completed, put it back
            if move_details.get('completed_sequence'):
                cs = move_details['completed_sequence']
                self.completed_sequences -= 1
                for i in range(13):
                    row = cs['row'] + i
                    col = cs['col']
                    self.cardsarray[row, col, 0] = cs['top_rank'] - i
                    self.cardsarray[row, col, 1] = cs['suit']
                    self.card_ids[row, col] = f"reconstructed-{row}-{col}"
                self.lastcard[col] = cs['row'] + 12
                
                # Remove from removedsuit tracking
                for i in range(9):
                    if self.removedsuit[i] == cs['suit']:
                        self.removedsuit[i] = 0
                        break
        
        elif move_details['type'] == 'deal':
            # Undo a card deal
            for card in reversed(move_details['cards_dealt']):
                self.cardsarray[card['row'], card['col']] = 0
                self.card_ids[card['row'], card['col']] = None
                self.nextcard -= 1
            
            # Restore last card positions
            self.lastcard = move_details['lastcards_before'].copy()
            self.dealnext10 -= 1
        
        self.historycount -= 1
        return self.get_game_state()
    
    def get_game_state(self) -> GameState:
        """Return current game state as Pydantic model"""
        piles = []
        for col in range(10):
            cards = []
            row = self.ROWBASE
            while row < 80 and self.cardsarray[row, col, 0] > 0:
                is_facedown = self.cardsarray[row, col, 0] == self.FACEDOWN
                card_id = self.card_ids[row, col]
                
                cards.append(Card(
                    rank=self.cardsarray[row, col, 0] if not is_facedown else self.facedown_cards[row, col, 0],
                    suit=self.cardsarray[row, col, 1] if not is_facedown else self.facedown_cards[row, col, 1],
                    is_face_up=not is_facedown,
                    id=card_id
                ))
                row += 1
                
            piles.append(Pile(
                cards=cards,
                last_card_index=self.lastcard[col]
            ))
        
        # Create stock (remaining cards)
        stock = []
        for card_pos in range(self.nextcard, 104):
            stock.append(Card(
                rank=self.deck[card_pos] % 13 + 1,
                suit=self.deck[card_pos] % 4 + 1,
                is_face_up=False,
                id=f"stock-{card_pos}"
            ))
        
        return GameState(
            piles=piles,
            stock=stock,
            completed_sequences=self.completed_sequences,
            moves=self.historycount,
            difficulty=9 - self.difficulty,
            draws_remaining=self.INITIAL_DEALS - self.dealnext10
        )

# Singleton game instance
game_instance = SpiderSolitaire()