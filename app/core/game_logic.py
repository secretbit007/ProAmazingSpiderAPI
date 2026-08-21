import numpy as np
import random
from uuid import uuid4
from typing import List
from app.schemas.game_state import GameState, Card, Pile

class SpiderSolitaire:
    def __init__(self):
        self.initialize_game()

    def initialize_game(self):
        self.states = []
        self.solve_events = []
        self.solve_snapshots: List[GameState] = []
        self._recording_solve_animation = False
        
        self.col = 0
        self.jmov = 0
        self.ia = 0
        self.ijj = 0
        self.j = 0
        self.blankcolumns = 0
        self.movecol = 0
        self.n = 0
        self.rowe = 0
        self.steplimit = 0  #
        self.cc = 0
        self.ct = 0

        self.dot = 0
        self.dott = 0

        self.fragment_length = 0
        self.xa = 0
        self.ya = 0

        self.jx = 0

        self.facedown = 15
        self.difficulty = 0
        self.suit_count = 4
        self.deal_seed = None

        self.cardrownumber = 0
        self.cardcolumn = 0
        self.cl = 0
        self.rw = 0
        self.rowbase = 5
        self.oldcolumn = 0
        self.oldrow = 0
        self.column = 0
        self.row = 0
        self.oldc = -1
        self.oldr = -1
        self.columnold = 0
        self.rowold = 0
        self.rowfordisplay = 0
        self.columnfordisplay = 0
        self.fromcolumn = 0
        self.fromrow = 0
        self.oldfromrow = 0
        self.colautostart = 0
        self.rowautostart = 0  # card variables
        self.nextcard = 0
        self.colsize = 30
        self.suitremoved = 0
        self.newtencards = 0  # control variables

        self.columnformove = 0
        self.totya = 0
        self.historysize = 1000
        self.u = np.zeros(shape=18, dtype='int32')
        self.dims = np.zeros(shape=18, dtype='int32')
        for jm in range(10):
            self.dims[jm] = jm
        self.removedsuit = np.zeros(shape=9, dtype='int32')

        self.lastcard = np.zeros(shape=10, dtype='int32')
        self.firstcard = np.zeros(shape=10, dtype='int32')
        self.suitcard = np.zeros(shape=10, dtype='int32')
        self.colmoves = np.zeros(shape=10, dtype='int32')
        self.histrec = np.zeros(shape=(self.historysize, 5), dtype='int32')
        self.xi = np.zeros(shape=23, dtype='int32')
        self.by = np.zeros(shape=23, dtype='int32')
        self.lth = np.zeros(shape=23, dtype='int32')
        self.lx = np.zeros(shape=23, dtype='int32')
        self.ly = np.zeros(shape=23, dtype='int32')
        self.blanks_program = np.zeros(shape=23, dtype='int32')
        self.ledgerow = np.zeros(shape=23, dtype='int32')

        self.ledgecolumn = np.zeros(shape=22, dtype='int32')
        self.blankcolumn = np.zeros(shape=23, dtype='int32')

        self.cardsarray = np.zeros(shape=(80, 10, 2), dtype='int32')  # Deal layout array

        self.caxsx = np.zeros(shape=(12, 10, 2), dtype='int32')

        self.dealnext10 = 0
        self.historycount = 0
        
        self.it = 0
        self.cds = np.zeros(shape=53, dtype='int32')
        self.card = np.zeros(shape=105, dtype='int32')
        self.dack = np.zeros(shape=(105), dtype='int32')
        self.dck = np.zeros(shape=(105), dtype='int32')
        self.newdig = np.zeros(shape=14, dtype='int32')
        self.oldmasthead = -1
        self.repsuity = 0

    def _card_suit(self, dck_value: int) -> int:
        """Map a deck index onto 1, 2, or 4 suits."""
        sc = self.suit_count if self.suit_count in (1, 2, 4) else 4
        if sc == 1:
            return 1
        if sc == 2:
            return (int(dck_value) % 2) + 1
        return (int(dck_value) % 4) + 1

    def export_internal_state(self) -> dict:
        return {
            "cardsarray": self.cardsarray.tolist(),
            "lastcard": self.lastcard.tolist(),
            "caxsx": self.caxsx.tolist(),
            "removedsuit": self.removedsuit.tolist(),
            "dck": self.dck.tolist(),
            "histrec": self.histrec.tolist(),
            "colmoves": self.colmoves.tolist(),
            "nextcard": int(self.nextcard),
            "dealnext10": int(self.dealnext10),
            "historycount": int(self.historycount),
            "difficulty": int(self.difficulty),
            "suit_count": int(self.suit_count),
            "deal_seed": self.deal_seed,
            "oldr": int(self.oldr),
            "oldc": int(self.oldc),
            "oldmasthead": int(self.oldmasthead),
        }

    def import_internal_state(self, data: dict) -> None:
        if "cardsarray" in data:
            self.cardsarray = np.array(data["cardsarray"], dtype="int32")
        if "lastcard" in data:
            self.lastcard = np.array(data["lastcard"], dtype="int32")
        if "caxsx" in data:
            self.caxsx = np.array(data["caxsx"], dtype="int32")
        if "removedsuit" in data:
            self.removedsuit = np.array(data["removedsuit"], dtype="int32")
        if "dck" in data:
            self.dck = np.array(data["dck"], dtype="int32")
        if "histrec" in data:
            self.histrec = np.array(data["histrec"], dtype="int32")
        if "colmoves" in data:
            self.colmoves = np.array(data["colmoves"], dtype="int32")
        self.nextcard = data.get("nextcard", 0)
        self.dealnext10 = data.get("dealnext10", 0)
        self.historycount = data.get("historycount", 0)
        self.difficulty = data.get("difficulty", 0)
        self.suit_count = data.get("suit_count", 4)
        self.deal_seed = data.get("deal_seed")
        self.oldr = data.get("oldr", -1)
        self.oldc = data.get("oldc", -1)
        self.oldmasthead = data.get("oldmasthead", -1)
        self.states = []

    def _clone_for_hint(self) -> "SpiderSolitaire":
        clone = SpiderSolitaire()
        clone.import_internal_state(self.export_internal_state())
        return clone


    def new(self):
        self.nextcard = 0
        self.historycount = 0
        self.dealnext10 = 0
        
        # Reset newdig array for difficulty logic
        for j in range(14):
            self.newdig[j] = 0

        self.shuffle()
        for i in range(10):
            if i < 9:
                self.removedsuit[i] = 0

            jk = self.rowbase
            i80 = self.dims[i]  #// 80

            while self.cardsarray[jk, i80, 0] > 0:
                jk = jk + 1

    def history(self, fromrow, fromcolumn, oldrow, oldcolumn, dot):  # ; // History, to enable Undo
        if oldcolumn > -1:
            self.historycount = self.historycount + 1
            if self.historycount == self.historysize + 1:
                self.historycount = 1

            self.histrec[self.historycount] = (oldrow, oldcolumn, fromrow, fromcolumn, dot)

    def find0(self, row, col80):
        col = col80  # // 80
        row2 = row
        while self.cardsarray[row2, col, 0] != 0:
            row2 = row2 + 1
        return row2

    def difficult(self, difficulty):
        self.difficulty = 9 - difficulty

        self.new()


    def shuffle(self):   #      2 pack deck before shuffle
        n = 0
        for i in range(1, 5):  # to 4
            m = 13 * (i - 1)
            for j in range(1, 14):
                n = n + 1
                self.card[n] = n
                self.cds[m + j] = j
                self.newdig[j] = 0  # Reset here as well for safety
        
        rng = random.Random(self.deal_seed)
        cdsleft = 52
        cdstrt = 1
        
        while cdsleft > 0:
            newrand = 0
            while newrand == 0:
                n = rng.randint(0, cdsleft - 1) + 1
                u = self.card[n] % 13 + 1   # card[n] is original ordered pack
                if cdsleft > 51 - self.difficulty:
                    if self.newdig[u] > 0:
                        newrand = 0
                    else:
                        self.newdig[u] = u   #  selects first n cards to be different
                        newrand = 1
                        self.dack[cdstrt] = self.card[n]

                        self.card[n] = self.card[cdsleft]
                        cdsleft = cdsleft - 1
                        cdstrt = cdstrt + 1
                else:
                    self.dack[cdstrt] = self.card[n]   # selects later cards from pack
                    self.card[n] = self.card[cdsleft]
                    cdsleft = cdsleft - 1
                    cdstrt = cdstrt + 1
                    newrand = 1

        for k in range(1, 53):  #  105
            self.dck[k] = self.dack[k]
            self.dck[k + 52] = self.dack[k]

        for k in range(1, 11):
            self.dck[64 + k] = self.dck[k + 44]  # dack[k+44]  # 54 instead of 64
            self.dck[44 + k] = self.dack[k]  # initial exposed cards
            self.dck[k] = self.dack[k + 12]  #  64

        self.nextcard = 0
        for jl in range(10):  # to 9 do
            il = self.rowbase
            while self.cardsarray[il, jl, 0] > 0:
                self.cardsarray[il, jl, 0] = 0  # card space empty
                il = il + 1
            
            if jl < 4:
                self.lastcard[jl] = self.rowbase + 5
            else:
                self.lastcard[jl] = self.rowbase + 4
                
        rowdepth = self.rowbase
        while rowdepth < self.rowbase + 7:
            for jl in range(10):
                jlo = jl

                if self.nextcard < 44 or (self.nextcard < 54 and rowdepth == self.rowbase + 7):
                    self.cardsarray[rowdepth, jlo, 0] = self.facedown
                    self.caxsx[rowdepth, jlo, 0] = self.dck[self.nextcard + 1] % 13 + 1
                    self.caxsx[rowdepth, jlo, 1] = self._card_suit(self.dck[self.nextcard + 1])
                    self.nextcard = self.nextcard + 1
                elif self.nextcard < 54:
                    self.cardsarray[rowdepth, jl, 0] = self.dck[self.nextcard + 1] % 13 + 1
                    self.cardsarray[rowdepth, jl, 1] = self._card_suit(self.dck[self.nextcard + 1])
                    self.nextcard = self.nextcard + 1

            rowdepth = rowdepth + 1

    def tencards(self):
        if self.it < 10:
            tenct = self.lastcard[self.it]  #  find0(tenct, it80)

            self.cardsarray[tenct + 1, self.it, 0] = self.dck[self.nextcard + 1] % 13 + 1
            self.cardsarray[tenct + 1, self.it, 1] = self._card_suit(self.dck[self.nextcard + 1])

            self.lastcard[self.it] = tenct + 1
            
            self.nextcard = self.nextcard + 1  # end; // End   Deals another 10 cards
            self.it = self.it + 1

    def stackclick(self):   #  Deals another 10 cards
        oldr = -1
        
        if self.dealnext10 < 5:
            self.newtencards = 1

            self.joinz()
            for self.it in range(10):
                self.tencards()

            self.newtencards = 0
            self.dealnext10 = self.dealnext10 + 1

            self.history(0, 0, 0, 1, 0)

    def undoes(self):
        if self.historycount > 0:
            self.oldrow, self.oldcolumn, self.fromrow, self.fromcolumn, dot = self.histrec[self.historycount]

            if (self.oldcolumn > 9) and (self.oldrow == -1):
                self.oldrow = self.oldrow
            else:
                self.historycount = self.historycount - 1

            kkk = 0
            if (dot == 1) and(self.fromrow + kkk > self.rowbase):  #  (dot == 1) and     310821
                self.cardsarray[self.fromrow + kkk - 1, self.fromcolumn, 0] = self.facedown

            if (self.oldrow == 0) and (self.oldcolumn == 1):
                self.dealnext10 = self.dealnext10 - 1

                for jm in range(10):       # undo deal10

                    i = jm

                    rowfordisplay = self.lastcard[i]  #find0(rowfordisplay, i80)

                    columnfordisplay = i
                    self.cardsarray[rowfordisplay, i, 0] = 0

                    rowfordisplay = rowfordisplay - 1
                    self.nextcard = self.nextcard - 1

                    self.lastcard[i] = rowfordisplay
            else:
                if self.oldrow == 0:                   # undo removeSuit
                    kk = 0
                    while kk < 8 and self.removedsuit[kk] > 0:
                        kk = kk + 1
                    kk = kk - 1
                    for jm in range(13):
                        i = jm + 1
                        self.cardsarray[self.fromrow + i - 1, self.fromcolumn, 0] = 14 - i
                        self.cardsarray[(self.fromrow + i - 1), self.fromcolumn, 1] = self.removedsuit[kk]
                        rowfordisplay = self.fromrow + i - 1
                        columnfordisplay = self.fromcolumn
                    self.lastcard[self.fromcolumn] = self.fromrow + 12
                    
                    self.removedsuit[kk] = 0

                else:
                    while (self.cardsarray[self.oldrow + kkk + 1, self.oldcolumn, 0] != 0) and (self.cardsarray[self.fromrow + kkk, self.fromcolumn, 0] == 0):
                        self.cardsarray[self.fromrow + kkk, self.fromcolumn, 0] = self.cardsarray[(self.oldrow + kkk + 1), self.oldcolumn, 0]
                        self.cardsarray[self.fromrow + kkk, self.fromcolumn, 1] = self.cardsarray[(self.oldrow + kkk + 1), self.oldcolumn, 1]
                        self.cardsarray[self.oldrow + kkk + 1, self.oldcolumn, 0] = 0

                        rowfordisplay = self.fromrow + kkk
                        columnfordisplay = self.fromcolumn

                        if (self.oldcolumn > 9) and self.oldrow + kkk + 1 != 6:  # oldcolumn>9 when suit has been removed - cols 10-17
                            rowfordisplay = self.oldrow + kkk + 1 - 1
                        else:
                            rowfordisplay = self.oldrow + kkk + 1
                        columnfordisplay = self.oldcolumn
                        
                        kkk = kkk + 1

                    self.lastcard[self.fromcolumn] = self.fromrow + kkk - 1
                    self.lastcard[self.oldcolumn] = self.oldrow


    def undo(self):
        self.oldr = -1
        self.undoes()

    def describe(self, icol):
        self.rowe = self.lastcard[icol]
        self.suitcard[icol] = self.cardsarray[self.rowe, self.col, 1]
        suitcardcol = self.suitcard[icol]
        if self.cardsarray[self.rowbase, self.col, 0] > 0:
            while (self.cardsarray[self.rowe - 1, self.col, 1] == suitcardcol) \
                    and (self.cardsarray[self.rowe, self.col, 0] == self.cardsarray[self.rowe - 1, self.col, 0] - 1):
                self.rowe = self.rowe - 1
        self.firstcard[icol] = self.rowe

    def movecards(self):  #  var     ki, kj: integer;
        if self.col < 10 or self.col > 9:
            oldrow = self.rowe
            fromrow = self.jx
            fromcolumn = self.ijj
            self.lastcard[fromcolumn] = fromrow - 1
    
            if self.lastcard[fromcolumn] != fromrow - 1 or fromcolumn > 9:
                fromrow = fromrow
            while self.cardsarray[self.jx, fromcolumn, 0] != 0:
                self.rowe = self.rowe + 1
                moved_rank = int(self.cardsarray[self.jx, fromcolumn, 0])
                moved_suit = int(self.cardsarray[self.jx, fromcolumn, 1])
                from_row_now = int(self.jx)
                to_row_now = int(self.rowe)

                self.cardsarray[self.rowe, self.col, 0] = self.cardsarray[self.jx, fromcolumn, 0]
                self.cardsarray[self.rowe, self.col, 1] = self.cardsarray[self.jx, fromcolumn, 1]
                self.cardsarray[self.jx, fromcolumn, 0] = 0  # // show vacant space after card has been moved
                self.jx = self.jx + 1

                self.solve_events.append({
                    "type": "move_card",
                    "from_row": from_row_now,
                    "from_col": int(fromcolumn),
                    "to_row": to_row_now,
                    "to_col": int(self.col),
                    "rank": moved_rank,
                    "suit": moved_suit,
                })
                if self._recording_solve_animation:
                    self.solve_snapshots.append(self.get_game_state())
            self.movecol = 1

            self.lastcard[self.col] = self.rowe
            
            dot = 0
            if self.cardsarray[fromrow - 1, fromcolumn, 0] > 0:
                if self.cardsarray[fromrow - 1, fromcolumn, 0] == self.facedown:  # // flip card when no longer covered by another card
                    dot = 1
                    self.cardsarray[fromrow - 1, fromcolumn, 0] = self.caxsx[fromrow - 1, fromcolumn, 0]
                    self.cardsarray[fromrow - 1, fromcolumn, 1] = self.caxsx[fromrow - 1, fromcolumn, 1]
                    self.solve_events.append({
                        "type": "flip_card",
                        "from_row": int(fromrow - 1),
                        "from_col": int(fromcolumn),
                        "to_row": int(fromrow - 1),
                        "to_col": int(fromcolumn),
                        "rank": int(self.cardsarray[fromrow - 1, fromcolumn, 0]),
                        "suit": int(self.cardsarray[fromrow - 1, fromcolumn, 1]),
                    })
                    if self._recording_solve_animation:
                        self.solve_snapshots.append(self.get_game_state())
                
            self.history(fromrow, fromcolumn, oldrow, self.col, dot)  # // history is stored to allow future undo
            movesize = self.jx - fromrow
            
            self.describe(self.col)
            self.col = fromcolumn
            self.describe(self.col)

    def joinsuits(self):
        self.jmov = 1
        for ijoins in range(9):
            self.iijoins = -1
            self.ijoins = 0
            while self.jmov == 1:
                self.jmov = 0
                self.joins()

    def joins(self):
        self.iijoins = self.iijoins + 1
        if self.iijoins == 10:
            self.ijoins = self.ijoins + 1
            self.iijoins = 0
        if self.ijoins < 10:
            if ((self.iijoins != self.ijoins) and (self.suitcard[self.ijoins] == self.suitcard[self.iijoins]) and
                    (self.cardsarray[self.firstcard[self.ijoins], self.ijoins, 0] > self.cardsarray[self.firstcard[self.iijoins], self.iijoins, 0]) and
                    (self.cardsarray[self.lastcard[self.ijoins], self.ijoins, 0] <= self.cardsarray[self.firstcard[self.iijoins], self.iijoins, 0] + 1) and
                    (self.cardsarray[self.lastcard[self.ijoins], self.ijoins, 0] > self.cardsarray[self.lastcard[self.iijoins], self.iijoins, 0])):
                self.jx = 0
                while self.cardsarray[self.firstcard[self.iijoins] + self.jx, self.iijoins, 0] >= self.cardsarray[self.lastcard[self.ijoins], self.ijoins, 0]:
                    self.jx = self.jx + 1

                self.rowe = self.lastcard[self.ijoins]
                self.jx = self.firstcard[self.iijoins] + self.jx
                self.col = self.ijoins
                self.ijj = self.iijoins
                self.movecards()
                self.jmov = 1
            else:
                self.jmov = 1

    def fillspaces(self): #   var     ijk, ij: integer;
        self.jmov = 1
        while self.jmov == 1:
            self.col = 10
            self.rowe = self.rowbase
            self.jmov = 0
            for ijk in range(10):
                ijk80 = self.dims[ijk]
                if self.cardsarray[self.rowbase, ijk, 0] == 0:
                    self.col = ijk
            if self.col < 10:  #  then // found empty column

                if self.dealnext10 < 5:

                    self.jx = 100
                    for ij in range(10):
                        if (self.firstcard[ij] < self.jx) and (self.firstcard[ij] > self.rowbase):

                            self.jx = self.firstcard[ij]  # // gets lowest FirstCard (early on)
                            self.ijj = ij
                else:
                    self.jx = self.rowbase
                    for ij in range(10):
                        if self.firstcard[ij] > self.jx:

                            self.jx = self.firstcard[ij]
                            self.ijj = ij  # // gets highest FirstCard (after 5 Deals of 10 cards)
                self.rowe = self.rowbase - 1
                if (self.jx > self.rowbase) and (self.jx != 100):

                    self.movecards()
                    self.col = self.ijj   # column with highest firstcard


    def joinz(self):
        for ijr in range(10):
            self.col = ijr
            self.describe(self.col)  # // gather data for each column
        self.movecol = 1  # // suggest a move has happened previously
        while self.movecol == 1:

            self.movecol = 0  #0  #   // show no move has happened yet in this iteration
            if self.newtencards == 0:  #    // if 10 more cards have been dealt, don't join suits.
                self.joinsuits()
            self.fillspaces()

    def solve(self):  # var   iii: integer;
        self.states.clear()
        self.solve_events.clear()
        self.solve_snapshots.clear()
        self.oldr = -1
        self._recording_solve_animation = True
        try:
            self.joinz()
        finally:
            self._recording_solve_animation = False


    def removesuit(self, row, colum):  #   // removecompletesuit from display
        suitremoved = 0
        clr = self.cardsarray[row, colum, 1]
        ij = 0
        while self.cardsarray[(row + ij), colum, 1] == clr and ij < 13:
            ij = ij + 1
        if ij == 13:

            ij = 0
            while self.removedsuit[ij] > 0:  # find next icon space
                ij = ij + 1
            self.removedsuit[ij] = clr

            self.oldcolumn = ij + 10

            for ij in range(13):  #  := 1 to 13 do

                self.cardsarray[row + 12 - ij, colum, 0] = 0

                rowfordisplay = row + 12 - ij
                columnfordisplay = colum
                
            suitremoved = 1
            self.lastcard[colum] = row - 1

            if (ij == 12):
                if self.cardsarray[row - 1, colum, 0] == self.facedown:
                    self.cardsarray[row - 1, colum, 0] = self.caxsx[row - 1, colum, 0]
                    self.cardsarray[row - 1, colum, 1] = self.caxsx[row - 1, colum, 1]
                    rowfordisplay = row - 1
                    columnfordisplay = colum

                    self.dot = 1
                elif self.cardsarray[row - 1, colum, 0] > 0:
                    rowfordisplay = row - 1
                    columnfordisplay = colum

            self.history(row, colum, 0, self.oldcolumn, self.dot)

        return suitremoved


    def findledges(self, colum):  #  find ledges and count available blank columns
        blankcolumns = 0
        for jl in range(22):
            self.ledgecolumn[jl] = -1

        for jl in range(10):
            ll = self.lastcard[jl] + 1

            i = self.cardsarray[ll - 1, jl, 0]
            self.ledgecolumn[i] = jl

            self.ledgerow[jl] = ll
            if (ll == self.rowbase) and (jl != colum):

                blankcolumns = blankcolumns + 1
                self.blankcolumn[blankcolumns] = jl
        return blankcolumns

    def steps(self, ia, fnd):  #   // find    available    shelves    for card movements
        find = fnd
        self.fromrow = self.lx[self.xa]
        self.fromcolumn = self.ly[self.xa]
        addr_end_fragment = self.fromrow
        ro80 = self.dims[self.fromcolumn]
        while self.cardsarray[addr_end_fragment, self.fromcolumn, 0] != 0:
            addr_end_fragment = addr_end_fragment + 1

        addr_end_fragment = addr_end_fragment - 1
        self.ct = addr_end_fragment
        self.n = 0
        self.xa = 0
        self.ya = 0
        self.fragment_length = 1
        while self.fromrow < addr_end_fragment:   #  while not bottom card

            while (self.ledgecolumn[self.cardsarray[addr_end_fragment, self.fromcolumn, 0] + 1] != -1) and (self.fromrow < addr_end_fragment):
                xx=self.cardsarray[addr_end_fragment, self.fromcolumn, 0] + 1
                self.ya = self.ya + 1
                self.lx[self.ya] = addr_end_fragment
                self.ly[self.ya] = self.fromcolumn
                self.by[self.ya] = 1
                self.lth[self.ya] = self.fragment_length
                self.fragment_length = 1
                addr_end_fragment = addr_end_fragment - 1
                self.n = 0

            if (self.cardsarray[addr_end_fragment, self.fromcolumn, 1] != self.cardsarray[addr_end_fragment - 1, self.fromcolumn, 1]) and (self.fromrow < addr_end_fragment):
                self.n = self.n + 1
                self.ya = self.ya + 1
                self.lx[self.ya] = addr_end_fragment
                self.ly[self.ya] = self.fromcolumn
                self.by[self.ya] = 0
                self.lth[self.ya] = self.fragment_length
                self.fragment_length = 1

            else:

                if self.fromrow < addr_end_fragment:
                    self.fragment_length = self.fragment_length + 1

            if self.n > ia:
                find = 0     #  not enough spaces, so invalidate
            addr_end_fragment = addr_end_fragment - 1

        self.ya = self.ya + 1
        self.lx[self.ya] = self.fromrow
        self.ly[self.ya] = self.fromcolumn
        self.by[self.ya] = 1
        self.lth[self.ya] = self.fragment_length
        return find

    def spacefind(self):  #  // find a space       var         jm: integer;
        stopper = 0
        jmx = 1
        while stopper == 0 and jmx < 11:
            if self.blankcolumn[jmx] < 10 and self.cardsarray[self.rowbase, self.blankcolumn[jmx], 0] == 0:
                stopper = 1
                self.oldcolumn = self.blankcolumn[jmx]
                self.oldrow = self.ledgerow[self.oldcolumn] - 1
            else:
                jmx = jmx + 1

    def cutstep(self):  #   // Reduce unnecessary steps
        self.cc = self.fromrow
        ro80 = self.dims[self.fromcolumn]

        self.cc = self.lastcard[ro80]
        self.ct = self.cc   # bottom of column

        while self.ct > self.fromrow:

            while (self.ct > self.fromrow) and (self.cardsarray[self.ct, self.fromcolumn, 1] == self.cardsarray[self.ct - 1, self.fromcolumn, 1]):
                self.ct = self.ct - 1   # if same suit, can be moved like a single card
            self.n = self.ct
            while (self.ledgecolumn[self.cardsarray[self.n, self.fromcolumn, 0] + 1] == -1) and (self.n < self.cc):
                self.n = self.n + 1
            while self.n < self.cc:

                self.n = self.n + 1
                self.ledgecolumn[self.cardsarray[self.n, self.fromcolumn, 0] + 1] = -1

            self.ct = self.ct - 1
            self.cc = self.ct

    def movecard(self):  #   // move a card(cardsArraySuit)       var         l: integer;
        self.columnformove = self.ly[self.xa]
        columnformove80 = self.dims[self.columnformove]
        ru80 = self.dims[self.oldcolumn]

        self.oldrow = self.find0(self.oldrow+1, ru80) - 1
        ll = 1
        if self.cardsarray[self.lx[self.xa] - 1, self.columnformove, 0] != self.facedown:
            self.dot = 0
        else:

            self.cardsarray[self.lx[self.xa] - 1, self.columnformove, 0] = self.caxsx[self.lx[self.xa] - 1, self.columnformove, 0]
            self.cardsarray[self.lx[self.xa] - 1, self.columnformove, 1] = self.caxsx[self.lx[self.xa] - 1, self.columnformove, 1]

            columnfordisplay = self.fromcolumn
            rowfordisplay = self.fromrow - 1
            
            self.dot = 1
            self.dott = 1
        rowfordisplay = self.lx[self.xa]
        columnfordisplay = self.columnformove

        while ll < self.lth[self.xa] + 1:

            lxxal = rowfordisplay + ll

            self.cardsarray[self.oldrow + ll, self.oldcolumn, 0] = self.cardsarray[(lxxal - 1), self.columnformove, 0]
            self.cardsarray[self.oldrow + ll, self.oldcolumn, 1] = self.cardsarray[(lxxal - 1), self.columnformove, 1]
            self.cardsarray[lxxal - 1, self.columnformove, 0] = 0

            ll = ll + 1

        movesize = ll - 1
        
        rowfordisplay = self.oldrow + 1
        columnfordisplay = self.oldcolumn

        self.lx[self.xa] = self.oldrow + 1
        self.ly[self.xa] = self.oldcolumn

    def mptyshlf(self):  #   // empty temporary shelf
        self.spacefind()
        self.movecard()
        if self.blanks_program[self.xa] == 1:

            self.oldrow = self.oldrow + self.lth[self.xa]
            self.xa = self.xa - 1
            self.movecard()
            self.xa = self.xa + 1

        if self.blanks_program[self.xa] == 2:

            self.oldrow = self.oldrow + self.lth[self.xa]
            self.xa = self.xa - 1
            self.movecard()
            self.xa = self.xa - 2
            self.spacefind()
            self.movecard()
            self.xa = self.xa + 1
            self.oldcolumn = self.ly[self.xa + 1]
            self.oldrow = self.lx[self.xa + 1] + self.lth[self.xa + 1] - 1
            self.movecard()
            self.oldrow = self.oldrow + self.lth[self.xa]
            self.xa = self.xa - 1
            self.movecard()
            self.xa = self.xa + 3

        if self.blanks_program[self.xa] == 3:

            self.oldrow = self.lx[self.xa - 4] + self.lth[self.xa - 4] - 1
            self.oldcolumn = self.ly[self.xa - 4]
            self.xa = self.xa - 5
            self.movecard()
            self.xa = self.xa + 5  #       // end proc mptyshlf;


    def fillshlf(self):  #   // fill temporary shelf
        self.oldrow = self.lastcard[self.oldcolumn]
        self.xa = self.xa - 1
        if self.blanks_program[self.xa] == 1:

            self.xa = self.xa - 1
            self.spacefind()
            self.movecard()
            self.xa = self.xa + 1

        if self.blanks_program[self.xa] == 2:

            self.xa = self.xa - 3
            self.spacefind()
            self.movecard()
            self.xa = self.xa + 1
            self.spacefind()
            self.movecard()
            self.oldrow = self.oldrow + self.lth[self.xa]
            self.xa = self.xa - 1
            self.movecard()
            self.xa = self.xa + 2
            self.spacefind()
            self.movecard()
            self.xa = self.xa + 1

        if self.blanks_program[self.xa] == 3:

            self.xa = self.xa - 5
            self.spacefind()
            self.movecard()
            self.xa = self.xa + 5

        self.oldcolumn = self.ly[self.xa + 1]
        self.oldrow = self.lx[self.xa + 1] + self.lth[self.xa + 1] - 1
        self.movecard()
        self.oldrow = self.oldrow + self.lth[self.xa]  #   // end proc fillshlf;

    def repeatcol(self):
        blnk = -1  # show no empty columns
        if self.oldr != self.column or self.oldc != self.fromrow:  # oldr, oldc are previous destination addr
            k = 0
            jl = 0    
            reprank = int(self.cardsarray[self.fromrow, self.column, 0]) + 1
            repsuit  = int(self.cardsarray[self.fromrow, self.column, 1])        
            while k < 10:
                j = self.lastcard[k]
                if j == 4:
                    blnk = k
                else:
                    m = int(self.cardsarray[j, k, 0])
                    if m == reprank:  
        
                        self.colmoves[jl] = k
                    
        
                        if self.cardsarray[j, k, 1] == repsuit:
    
                            j = int(self.colmoves[0])
                            self.colmoves[0] = k
                            self.colmoves[jl] = j
                        jl = jl + 1
                k = k + 1
            self.masthead = jl - 1

            if blnk != -1:
                self.colmoves[jl] = blnk

                self.masthead = self.masthead + 1
    
            j = int(self.colmoves[0])
    
            self.oldmasthead = 0
            self.colmoves[9] = self.column
            self.colmoves[8] = self.fromrow
            return j

        else:   # same card was clicked again
            colum = int(self.colmoves[9])
            fromro = int(self.colmoves[8])
            if self.cardsarray[fromro - 1, colum, 0] == self.cardsarray[self.fromrow, self.column, 0] + 1 or fromro == 5:
                self.colmoves[self.masthead + 1] = colum
                self.masthead = self.masthead + 1
            self.colmoves[8] = 0
        
            if self.oldmasthead == self.masthead:
                j = int(self.colmoves[0])
                self.oldmasthead = 0
            else:
                self.oldmasthead = self.oldmasthead + 1
                j = int(self.colmoves[self.oldmasthead])
    
            return j

    def autos(self, row):   #// start proc autos;   // calculate path for card movements
        xi = np.zeros(shape=23, dtype='int32')  # [0] * 23
        self.suitremoved = 0         # show whole suit not removed
        kill = 0                # show move valid so far
        ia = 0
        colautostart = self.column          # clicked column
        r80 = self.dims[self.column]
        rowautostart = row
        if self.cardsarray[self.rowbase, self.column, 0] != 0:   #  is column blank?
            ia = self.lastcard[r80]
            samesuitlgth = 1
            self.cc = row
            samesuit = self.cardsarray[self.cc, self.column, 1]   #  set suit
            while self.cc < ia and self.cardsarray[self.cc + 1, self.column, 0] + 1 == self.cardsarray[self.cc, self.column, 0]:
                samesuitlgth = samesuitlgth + 1
                self.cc = self.cc + 1  #   check whether lower cards are in numerical sequence and
                if self.cardsarray[self.cc, self.column, 1] != samesuit:
                    samesuit = 0
            if self.cc != ia:    # if not, invalidate the move
                kill = 1

            if ia - row == 12 and kill == 0:
                self.suitremoved = self.removesuit(row, self.column)  #    // test whether can remove completed suit of 13
            if self.suitremoved == 1:
                self.column = -1       # suit removed, so therefore invalidate further processing of click
                kill = 1
        else:
            kill = 1

        self.fromrow = row  #   // fromrow,fromcolumn is addr of card to be moved
        self.fromcolumn = self.column
        fromrank = self.cardsarray[self.fromrow, self.fromcolumn, 0]

        if kill == 0:

            self.column = self.repeatcol()  #  finds a column for clicked card to move to. rankjoin will equal that column, samesuitjoin if same suit

        r80 = self.dims[self.column]
        if self.column == -1:  #         // no possible destination for cardsArrayRank[fromrow,fromcolumn]
            kill = 1

        else:

            if self.cardsarray[self.rowbase, self.column, 0] == 0:  # empty column
                row = self.rowbase - 1

                cji = self.facedown  # used for later testing
            else:
                row = self.lastcard[r80]
                cji = self.cardsarray[row, self.column, 0] - 1

            if (row > self.rowbase - 1) or (self.cardsarray[self.fromrow, self.fromcolumn, 0] == 0):

                self.ct = self.fromrow
            if ((self.cardsarray[self.fromrow, self.fromcolumn, 0] == cji) or (self.cardsarray[row, self.column, 0] == 0)) and (kill == 0):
                found = 1  # a destination for the card(s) may be a blank column
            else:
                kill = 1   #  invalidate
                found = 0
            if self.suitremoved == 1:
                found = 0
            if found == 1:

                self.dott = 0
                blankcolumns = self.findledges(self.column)   #  find available empty working columns
                self.ledgecolumn[self.cardsarray[self.fromrow, self.fromcolumn, 0] + 1] = self.column
                ia = blankcolumns * blankcolumns - blankcolumns + 1  #  // dynamic potential of blank columns

                if blankcolumns == 0:
                    ia = 0
                self.cc = self.fromrow
                while self.cc <= self.ct:
                    self.cc = self.cc + 1
                self.xa = 1

                self.lx[self.xa] = self.fromrow
                self.ly[self.xa] = self.fromcolumn

                self.cutstep()     # find all the ledges and blank columns
                found = self.steps(ia, found)            # necessary to move the card(s)

                if found == 0:
                    kill = 1                  # not enough spaces so invalidate

                if found == 1:
                    self.oldc = row + 1  #  save valid destination in case there are more destinations for later attempts
                    self.oldr = self.column
    
                short = self.lastcard[self.fromcolumn] - self.fromrow + 1
                if found == 1:
                    if samesuit != samesuit:
                        ijjj = 0
                        while ijjj < short:
                            self.cardsarray[row + 1 + ijjj, self.column, 0] = self.cardsarray[self.fromrow + ijjj, self.fromcolumn, 0]
                            self.cardsarray[row + 1 + ijjj, self.column, 1] = self.cardsarray[self.fromrow + ijjj, self.fromcolumn, 1]
                            
                            self.cardsarray[self.fromrow + ijjj, self.fromcolumn, 0] = 0
                            ijjj = ijjj + 1

                        if self.cardsarray[self.fromrow - 1, self.fromcolumn, 0] == self.facedown:
                            self.cardsarray[self.fromrow - 1, self.fromcolumn, 0] = self.caxsx[self.fromrow - 1, self.fromcolumn, 0]
                            self.cardsarray[self.fromrow - 1, self.fromcolumn, 1] = self.caxsx[self.fromrow - 1, self.fromcolumn, 1]
                            
                            self.dot = 1
                            self.dott = 1
                        else:
                            self.dot = 0
                        self.lastcard[self.column] = self.lastcard[self.column] + short
                        self.lastcard[self.fromcolumn] = self.lastcard[self.fromcolumn] - short
                        self.states.append(self.get_game_state())
                        self.history(self.fromrow, self.fromcolumn, row, self.column, self.dot)
                    else:
                        for jk in range(1, self.ya+1):  #   Prepare tables to enable moving the cards
                            self.blanks_program[jk] = 0
                            xi[jk] = 0
                        yy = self.ya
                        self.by[0] = 1
                        self.ly[0] = 10
                        self.xa = 1
                        while self.xa < self.ya:
                            j = 0
                            ia = 0
                            while self.by[self.xa] == 0:
                                ia = ia + 1
                                j = j + self.lth[self.xa]
                                xi[ia] = self.xa
                                self.xa = self.xa + 1
                            if ia == blankcolumns + 1:   # set up program for dynamic use of blank columns
                                self.blanks_program[xi[2]] = 1  # 1 empty column short
                            elif ia == blankcolumns + 2:   # 2 empty columns short
                                self.blanks_program[xi[2]] = 1
                                self.blanks_program[xi[4]] = 1
                            elif ia == blankcolumns + 3:  # 3 empty columns short
                                self.blanks_program[xi[2]] = 1
                                self.blanks_program[xi[4]] = 2
                            elif ia == blankcolumns + 4:   #  4 empty columns short  etc
                                self.blanks_program[xi[2]] = 1
                                self.blanks_program[xi[4]] = 2
                                self.blanks_program[xi[6]] = 1
                            elif ia == blankcolumns + 5:
                                self.blanks_program[xi[2]] = 1
                                self.blanks_program[xi[4]] = 2
                                self.blanks_program[xi[6]] = 1
                                self.blanks_program[xi[8]] = 1
                            elif ia == blankcolumns + 6:
                                self.blanks_program[xi[2]] = 1
                                self.blanks_program[xi[4]] = 2
                                self.blanks_program[xi[6]] = 1
                                self.blanks_program[xi[8]] = 2
                            elif ia == blankcolumns + 7:
                                self.blanks_program[xi[2]] = 1
                                self.blanks_program[xi[4]] = 2
                                self.blanks_program[xi[6]] = 1
                                self.blanks_program[xi[8]] = 2
                                self.blanks_program[xi[10]] = 1
                            elif ia == (blankcolumns + 8):
                                self.blanks_program[xi[3]] = 1
                                self.blanks_program[xi[5]] = 2
                                self.blanks_program[xi[6]] = 3
                                self.blanks_program[xi[7]] = 1
                                self.blanks_program[xi[9]] = 2
                                self.blanks_program[xi[11]] = 1
                            self.xa = self.xa + 1

                        self.xa = 0
                        while self.xa < yy:
                            self.xa = self.xa + 1
                            columnformove = self.dims[self.ly[self.xa]]  #// 80
                            self.oldcolumn = self.ledgecolumn[self.cardsarray[self.lx[self.xa], columnformove, 0] + 1]
                            if self.oldcolumn == -1:
                                self.mptyshlf()
                            else:
                                self.oldrow = self.ledgerow[self.oldcolumn] - 1
                                self.movecard()
                                self.oldrow = self.oldrow + self.lth[self.xa]
                                xxx = self.xa
                                while self.by[self.xa - 1] == 0:
                                    self.fillshlf()
                                self.xa = xxx

                            self.states.append(self.get_game_state())
                        olru = self.oldcolumn
                        olcu = self.oldrow
                        while self.xa > 0:
                            while (self.xa > 0) and (self.ly[self.xa] == self.oldcolumn):
                                self.xa = self.xa - 1
                            xx = self.xa
                            if (self.xa > 0) and (self.ly[self.xa] != self.ly[self.xa - 1]):
                                self.oldcolumn = olru
                                ru80 = self.dims[self.oldcolumn]
                                self.oldrow = olcu
                                self.oldrow = self.lastcard[ru80]
                                self.movecard()
                                self.oldrow = self.oldrow + self.lth[self.xa]
                            else:
                                if self.xa > 0:
                                    while (self.ly[xx] == self.ly[self.xa]) and (self.xa > 0):
                                        self.xa = self.xa - 1
                                    self.xa = self.xa + 1
                                    while self.xa < xx:
                                        self.mptyshlf()
                                        self.xa = self.xa + 1
                                    self.oldcolumn = olru
                                    ru80 = self.dims[self.oldcolumn]
                                    self.oldrow = olcu

                                    self.oldrow = self.lastcard[ru80]
                                    self.movecard()
                                    self.oldrow = self.oldrow + self.lth[self.xa]
                                    while self.by[self.xa - 1] == 0:
                                        self.fillshlf()

                                    self.oldcolumn = olru

                            self.states.append(self.get_game_state())

                        self.lastcard[self.column] = self.lastcard[self.column] + self.lastcard[colautostart] - self.fromrow + 1
                        self.lastcard[self.fromcolumn] = self.fromrow - 1
                        self.states.append(self.get_game_state())

                        self.n = 1
                        self.cc = row
                        if found == 1:

                            if self.suitremoved == 0:
                                self.history(self.fromrow, self.fromcolumn, row, self.oldcolumn, self.dott)

    def cardfrontclick(self, rw, cl):  #  (ACard: TFunnelWebPlayingCard);var   lcoordinates: TRowAndColumn;
        self.states.clear()
        self.column = cl   #  column
        row = rw + self.rowbase - 1   #  row
        
        self.autos(row)  #   //compute whether move legal

        self.suitremoved = 0

    def suggest_hint(self) -> dict:
        """Find one legal tap without mutating this instance."""
        candidates = []
        for col in range(10):
            last = int(self.lastcard[col])
            if last < self.rowbase:
                continue
            row = last
            while row >= self.rowbase:
                rank = int(self.cardsarray[row, col, 0])
                if rank == 0 or rank == self.facedown:
                    break
                from_row = row - self.rowbase + 1
                candidates.append((from_row, col))
                if row == self.rowbase:
                    break
                above = int(self.cardsarray[row - 1, col, 0])
                if above == 0 or above == self.facedown or above != rank + 1:
                    break
                row -= 1

        best = None
        reason_rank = {"complete_suit": 3, "same_suit": 2, "rank": 1, "empty": 0}
        for from_row, col in candidates:
            clone = self._clone_for_hint()
            clone.oldr = -1
            clone.oldc = -1
            clone.oldmasthead = -1
            before_last = clone.lastcard.copy()
            before_removed = int(np.count_nonzero(clone.removedsuit))
            clone.cardfrontclick(rw=from_row, cl=col)
            after_removed = int(np.count_nonzero(clone.removedsuit))
            changed = not np.array_equal(clone.cardsarray, self.cardsarray)
            if not changed:
                continue
            to_col = None
            reason = "rank"
            if after_removed > before_removed:
                reason = "complete_suit"
            else:
                for k in range(10):
                    if k != col and int(clone.lastcard[k]) > int(before_last[k]):
                        to_col = k
                        dest_row = int(before_last[k])
                        if dest_row < clone.rowbase:
                            reason = "empty"
                        else:
                            src_suit = int(self.cardsarray[from_row + self.rowbase - 1, col, 1])
                            dest_suit = int(self.cardsarray[dest_row, k, 1])
                            reason = "same_suit" if src_suit == dest_suit else "rank"
                        break
                if to_col is None:
                    reason = "empty"
            score = reason_rank.get(reason, 0)
            pick = {
                "from_row": from_row,
                "from_col": col,
                "to_col": to_col,
                "reason": reason,
                "score": score,
            }
            if best is None or pick["score"] > best["score"] or (
                pick["score"] == best["score"] and from_row < best["from_row"]
            ):
                best = pick

        if best is None:
            return {
                "from_row": None,
                "from_col": None,
                "to_col": None,
                "reason": "none",
                "message": "No moves right now — try Deal.",
            }

        messages = {
            "complete_suit": "Tap this King to clear a completed suit.",
            "same_suit": "Build this onto the same suit.",
            "rank": "This card can drop onto the matching rank.",
            "empty": "Move this card into an empty column.",
        }
        return {
            "from_row": best["from_row"],
            "from_col": best["from_col"],
            "to_col": best["to_col"],
            "reason": best["reason"],
            "message": messages.get(best["reason"], "Try this card."),
        }

    def new_game(self, difficulty, suit_count=4, seed=None):
        self.initialize_game()

        for jm in range(17):

            if jm < 10:
                self.dims[jm] = jm  # * 80
            else:
                self.dims[jm] = 0
        clamped = max(0, min(9, int(difficulty)))
        self.difficulty = 9 - clamped
        self.suit_count = suit_count if suit_count in (1, 2, 4) else 4
        self.deal_seed = seed

        self.new()

    
    def get_game_state(self) -> GameState:
        # Convert cardsarray to piles
        piles = []
        for col in range(10):  # There are 10 columns in spider solitaire
            pile_cards = []
            row = self.rowbase
            last_card_index = -1  # Will store the index of the last movable card

            while row < 80 and self.cardsarray[row, col, 0] != 0:  # 0 means no card
                rank = self.cardsarray[row, col, 0]
                suit = self.cardsarray[row, col, 1]
                face_up = True if rank != self.facedown else False
                
                if face_up:
                    # For face-up cards, use the actual rank and suit
                    pile_cards.append(Card(rank=rank, suit=suit, is_face_up=True))

                    if row == self.lastcard[col]:
                        last_card_index = len(pile_cards)
                else:
                    # For face-down cards, we don't know the actual rank/suit yet
                    # But we can get them from caxsx if needed
                    pile_cards.append(Card(rank=0, suit=0, is_face_up=False))
                
                row += 1

            # If no face-up cards found, set last_card_index to -1
            if last_card_index == -1 and pile_cards:
                last_card_index = len(pile_cards) - 1 if pile_cards[-1].is_face_up else -1

            piles.append(Pile(cards=pile_cards, last_card_index=last_card_index))
        
        # Remaining stock: expose count only (avoids huge JSON arrays on every response).
        remaining_cards = max(0, 104 - self.nextcard)  # Total cards in 2 decks minus dealt cards

        # Count completed sequences (removed suits)
        completed_sequences = 0
        completed_sequences_by_suit = {}
        for suit in self.removedsuit:
            if suit > 0:
                completed_sequences += 1
                # Count how many times each suit has been completed
                if suit in completed_sequences_by_suit:
                    completed_sequences_by_suit[suit] += 1
                else:
                    completed_sequences_by_suit[suit] = 1
        
        # Calculate remaining draws (each draw is 10 cards)
        draws_remaining = 5 - self.dealnext10
        
        return GameState(
            piles=piles,
            stock=[],
            stock_count=remaining_cards,
            completed_sequences=completed_sequences,
            completed_sequences_by_suit=completed_sequences_by_suit,
            moves=self.historycount,
            difficulty=9 - self.difficulty,  # Convert internal difficulty to external
            draws_remaining=draws_remaining,
            suit_count=self.suit_count if self.suit_count in (1, 2, 4) else 4,
            seed=self.deal_seed,
        )

# Singleton game instance
game_instance = SpiderSolitaire()
