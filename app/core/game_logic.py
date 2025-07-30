import numpy as np
import random
import uuid
from typing import Dict, List, Tuple, Optional
from pydantic import BaseModel
from app.schemas.game_state import Card, Pile, GameState

class SpiderSolitaire:
    # Constants
    FACEDOWN = 15
    ROWBASE = 5
    HISTORY_SIZE = 1000
    INITIAL_DEALS = 5
    
    def __init__(self):
        self.initialize_game()
        
    def initialize_game(self):
        # Initialize numpy arrays for game state
        self.cardsarray = np.zeros((80, 10, 2), dtype='int32')  # Main game board
        self.card_ids = np.empty((80, 10), dtype='object')      # Card unique IDs
        self.colms = np.zeros((80, 10), dtype='int32')          # Column positions
        self.completed_sequences = 0                            # Count of completed suits
        self.lastcard = np.zeros(10, dtype='int32')             # Last card in each column
        self.histrec = np.zeros((self.HISTORY_SIZE, 5), dtype='int32')  # Move history
        self.deck = np.zeros(105, dtype='int32')                # Deck storage
        
        # Game state variables
        self.nextcard = 0               # Next card to deal
        self.historycount = 0           # Move counter
        self.dealnext10 = 0             # Number of deals completed
        self.redalert = 0               # Error state flag
        
        # Facedown card storage
        self.facedown_cards = np.zeros((80, 10, 2), dtype='int32')
        self.facedown_ids = np.empty((80, 10), dtype='object')
    
    def new_game(self, difficulty: int = 9):
        """Start a new game with specified difficulty (0-9)"""
        self.difficulty = 9 - difficulty
        self.initialize_game()
        self.shuffle()
        self.setup_initial_deal()
        return self.get_game_state()
    
    def shuffle(self):
        """Shuffle the deck (2 packs)"""
        # Initialize card values (1-52 for first pack, 53-104 for second)
        self.deck = np.array([(i % 52) + 1 for i in range(104)], dtype='int32')
        
        # For difficulty, ensure we have one complete suit of each color showing
        newdig = np.zeros(14, dtype='int32')
        random.seed(78)  # Fixed seed for reproducibility
        
        # First 8 cards (difficulty-based) must be unique ranks
        if self.difficulty < 9:
            unique_positions = random.sample(range(52), 8)
            for pos in unique_positions:
                rank = self.deck[pos] % 13 + 1
                while rank in newdig:
                    np.random.shuffle(self.deck[:52])
                    rank = self.deck[pos] % 13 + 1
                newdig[pos % 8] = rank
        
        # Shuffle both halves of the deck
        np.random.shuffle(self.deck[:52])
        np.random.shuffle(self.deck[52:104])
        
        # Move some cards to the front for initial deal
        self.deck[:12] = self.deck[44:56]
        self.deck[44:56] = self.deck[12:24]
    
    def setup_initial_deal(self):
        """Deal initial cards"""
        self.nextcard = 0
        for jl in range(10):
            # Initialize column positions
            il = self.ROWBASE
            while il < 80:
                self.colms[il, jl] = il - self.ROWBASE + self.ROWBASE
                il += 1
            
            # Set initial last card positions
            self.lastcard[jl] = self.ROWBASE + (5 if jl < 4 else 4)
                
        # Deal initial cards
        rowdepth = self.ROWBASE
        while rowdepth < self.ROWBASE + 7:
            for jl in range(10):
                card_id = str(uuid.uuid4())
                if self.nextcard < 44 or (self.nextcard < 54 and rowdepth == self.ROWBASE + 7):
                    # Deal facedown cards
                    self.cardsarray[rowdepth, jl, 0] = self.FACEDOWN
                    self.facedown_cards[rowdepth, jl, 0] = self.deck[self.nextcard] % 13 + 1
                    self.facedown_cards[rowdepth, jl, 1] = self.deck[self.nextcard] % 4 + 1
                    self.facedown_ids[rowdepth, jl] = card_id
                    self.nextcard += 1
                elif self.nextcard < 54:
                    # Deal faceup cards
                    self.cardsarray[rowdepth, jl, 0] = self.deck[self.nextcard] % 13 + 1
                    self.cardsarray[rowdepth, jl, 1] = self.deck[self.nextcard] % 4 + 1
                    self.card_ids[rowdepth, jl] = card_id
                    self.nextcard += 1
            rowdepth += 1
    
    def get_game_state(self) -> GameState:
        """Return current game state as Pydantic model"""
        piles = []
        for i in range(10):
            cards = []
            j = self.ROWBASE
            while j < 80 and self.cardsarray[j, i, 0] > 0:
                is_facedown = self.cardsarray[j, i, 0] == self.FACEDOWN
                card_id = self.facedown_ids[j, i] if is_facedown else self.card_ids[j, i]
                
                cards.append(Card(
                    rank=self.cardsarray[j, i, 0] if not is_facedown else self.facedown_cards[j, i, 0],
                    suit=self.cardsarray[j, i, 1] if not is_facedown else self.facedown_cards[j, i, 1],
                    is_face_up=not is_facedown,
                    id=card_id
                ))
                j += 1
                
            piles.append(Pile(
                cards=cards,
                last_card_index=self.lastcard[i]
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
    
    def is_valid_move(self, from_row: int, from_col: int, to_row: int, to_col: int) -> bool:
        """Check if move is valid"""
        # Basic validation
        if from_col == to_col:
            return False
        
        if self.cardsarray[from_row, from_col, 0] == 0:
            return False
            
        # Check if destination is empty column
        if self.cardsarray[self.ROWBASE, to_col, 0] == 0:
            return True
            
        # Check if moving to a valid sequence
        to_card_rank = self.cardsarray[self.lastcard[to_col], to_col, 0]
        from_card_rank = self.cardsarray[from_row, from_col, 0]
        
        return to_card_rank == from_card_rank + 1
    
    def execute_move(self, from_row: int, from_col: int, to_row: int, to_col: int):
        """Execute a valid move"""
        move_length = 0
        current_row = from_row
        
        # Calculate how many cards to move
        while (current_row < 80 and 
               self.cardsarray[current_row, from_col, 0] != 0 and
               (current_row == from_row or 
                (self.cardsarray[current_row, from_col, 0] == self.cardsarray[current_row-1, from_col, 0] - 1 and
                 self.cardsarray[current_row, from_col, 1] == self.cardsarray[current_row-1, from_col, 1]))):
            move_length += 1
            current_row += 1
        
        # Perform the move
        for i in range(move_length):
            # Move card data
            self.cardsarray[to_row + i + 1, to_col, 0] = self.cardsarray[from_row + i, from_col, 0]
            self.cardsarray[to_row + i + 1, to_col, 1] = self.cardsarray[from_row + i, from_col, 1]
            
            # Move card ID
            if self.cardsarray[from_row + i, from_col, 0] == self.FACEDOWN:
                self.facedown_ids[to_row + i + 1, to_col] = self.facedown_ids[from_row + i, from_col]
            else:
                self.card_ids[to_row + i + 1, to_col] = self.card_ids[from_row + i, from_col]
            
            # Clear source position
            self.cardsarray[from_row + i, from_col, 0] = 0
        
        # Update last card positions
        self.lastcard[to_col] = to_row + move_length
        self.lastcard[from_col] = from_row - 1
        
        # Check if we revealed a facedown card
        if (from_row > self.ROWBASE and 
            self.cardsarray[from_row - 1, from_col, 0] == self.FACEDOWN):
            self.cardsarray[from_row - 1, from_col, 0] = self.facedown_cards[from_row - 1, from_col, 0]
            self.cardsarray[from_row - 1, from_col, 1] = self.facedown_cards[from_row - 1, from_col, 1]
            self.card_ids[from_row - 1, from_col] = self.facedown_ids[from_row - 1, from_col]
        
        # Check for completed suits
        self.check_completed_suits()
        self.historycount += 1
    
    def make_move(self, from_row: int, from_col: int, to_row: Optional[int] = None, to_col: Optional[int] = None):
        """Make a move in the game"""
        if from_col < 0 or from_col > 9 or from_row < self.ROWBASE or from_row > 79:
            raise ValueError("Invalid move coordinates")
            
        if to_col is None:
            # Auto-move logic
            self.cardfrontclick(from_row, from_col)
        else:
            # Specific move
            if to_col < 0 or to_col > 9:
                raise ValueError("Invalid destination column")
                
            if self.is_valid_move(from_row, from_col, to_row, to_col):
                self.execute_move(from_row, from_col, to_row, to_col)
    
    def check_completed_suits(self):
        """Check for and remove completed suits"""
        for col in range(10):
            if self.lastcard[col] - self.ROWBASE + 1 >= 13:
                top_row = self.lastcard[col] - 12
                suit = self.cardsarray[top_row, col, 1]
                complete = True
                
                # Check if we have 13 consecutive cards of same suit
                for i in range(13):
                    if (self.cardsarray[top_row + i, col, 0] != self.cardsarray[top_row, col, 0] - i or
                        self.cardsarray[top_row + i, col, 1] != suit):
                        complete = False
                        break
                
                if complete:
                    self.remove_completed_suit(top_row, col, suit)
    
    def remove_completed_suit(self, row: int, col: int, suit: int):
        """Remove a completed suit from the board"""
        self.completed_sequences += 1
        
        # Remove cards from column
        for i in range(13):
            self.cardsarray[row + i, col, 0] = 0
        
        self.lastcard[col] = row - 1
        
        # Flip facedown card if revealed
        if row > self.ROWBASE and self.cardsarray[row - 1, col, 0] == self.FACEDOWN:
            self.cardsarray[row - 1, col, 0] = self.facedown_cards[row - 1, col, 0]
            self.cardsarray[row - 1, col, 1] = self.facedown_cards[row - 1, col, 1]
            self.card_ids[row - 1, col] = self.facedown_ids[row - 1, col]
    
    def deal_cards(self):
        """Deal 10 more cards from the stack"""
        if self.dealnext10 >= self.INITIAL_DEALS:
            raise ValueError("No more cards to deal")
            
        for i in range(10):
            if self.nextcard >= 104:
                raise ValueError("No more cards in deck")
                
            col = i
            target_row = self.lastcard[col] + 1
            self.cardsarray[target_row, col, 0] = self.deck[self.nextcard] % 13 + 1
            self.cardsarray[target_row, col, 1] = self.deck[self.nextcard] % 4 + 1
            self.card_ids[target_row, col] = str(uuid.uuid4())
            self.lastcard[col] = target_row
            self.nextcard += 1
        
        self.dealnext10 += 1
        self.historycount += 1
    
    def solve(self):
        """Let the AI solve moves"""
        moved = True
        while moved:
            moved = False
            self.check_completed_suits()
            
            for from_col in range(10):
                if self.cardsarray[self.ROWBASE, from_col, 0] == 0:
                    continue
                    
                from_row = self.lastcard[from_col]
                card_rank = self.cardsarray[from_row, from_col, 0]
                card_suit = self.cardsarray[from_row, from_col, 1]
                
                for to_col in range(10):
                    if from_col == to_col:
                        continue
                        
                    if self.cardsarray[self.ROWBASE, to_col, 0] == 0:
                        try:
                            self.make_move(from_row, from_col, self.ROWBASE, to_col)
                            moved = True
                            break
                        except:
                            continue
                    
                    to_row = self.lastcard[to_col]
                    to_rank = self.cardsarray[to_row, to_col, 0]
                    to_suit = self.cardsarray[to_row, to_col, 1]
                    
                    if to_rank == card_rank + 1 and to_suit == card_suit:
                        try:
                            self.make_move(from_row, from_col, to_row, to_col)
                            moved = True
                            break
                        except:
                            continue
            
            if not moved and self.dealnext10 < self.INITIAL_DEALS:
                self.deal_cards()
                moved = True
    
    def undo_move(self):
        """Undo the last move"""
        if self.historycount <= 0:
            raise ValueError("No moves to undo")
            
        self.historycount -= 1
        # Implementation would need to track move history
    
    def cardfrontclick(self, row: int, col: int):
        """Handle card click (original autos logic)"""
        if col < 0 or col > 9:
            return
            
        if self.cardsarray[row, col, 0] == 0:
            return
            
        card_rank = self.cardsarray[row, col, 0]
        card_suit = self.cardsarray[row, col, 1]
        
        for dest_col in range(10):
            if dest_col == col:
                continue
                
            if self.cardsarray[self.ROWBASE, dest_col, 0] == 0:
                self.make_move(row, col, self.ROWBASE, dest_col)
                return
                
            dest_row = self.lastcard[dest_col]
            dest_rank = self.cardsarray[dest_row, dest_col, 0]
            dest_suit = self.cardsarray[dest_row, dest_col, 1]
            
            if dest_rank == card_rank + 1 and dest_suit == card_suit:
                self.make_move(row, col, dest_row, dest_col)
                return
        
        self.redalert = 1

# Singleton game instance
game_instance = SpiderSolitaire()