import typing
import copy
import time

# getBlockNum() returns the block number (1-9) of the associated i and j coordinates
def getBlockNum(i, j):
    if i <= 3:
        if j <= 3:
            return 1
        elif j <= 6:
            return 2
        else:
            return 3
    elif i <= 6:
        if j <= 3:
            return 4
        elif j <= 6:
            return 5
        else:
            return 6
    else:
        if j <= 3:
            return 7
        elif j <= 6:
            return 8
        else:
            return 9

class Tile:
    def __init__(self,x,y,block,entry):
        self.x = x
        self.y = y
        self.block = block
        self.entry = entry
        self.domain = {1,2,3,4,5,6,7,8,9}

    def __eq__(self, other) -> bool:
        return self.x == other.x and self.y == other.y

    def __gt__(self, other) -> bool:
        if self.x == other.x:
            return self.y < other.y
        else:
            return self.x < other.x

    def updateDomain(self, entry):
        self.domain.discard(entry)
            
    def domainEmpty(self) -> bool:
        if len(self.domain) or self.entry != None:
            return False
        return True

    def getPosition(self): # -> tuple[int,int]:
        return Position(self.x, self.y)

    def placeEntry(self) -> int:
        nextValue = min(self.domain)
        self.entry = nextValue
        return nextValue

#Sudoku CSP:
#   Variables: Each board tile
#   Domain: 1-9
#   Constraints: row, column, and block constraints
#   Goal: Assign a value to each variable without violating constraints
class Position:
    def __init__(self, row, col):
        self.row = row
        self.col = col

count = 0

class Board:
    def __init__(self, startingState):
        # 9x9 board flattened
        self.size = 81
        self.unassigned = self.size

        board = []
        for i in range(9):
            for j in range(9):
                board.append(Tile(i+1, j+1, getBlockNum(i+1, j+1), None))
        # none signifies empty space
        self.board = board
        self.placeTiles(startingState)

    # this function is used to print out the current state of the sudoku board
    def __str__(self):
        print("_____________________________________")
        for i in range(9):
            row_string = "| "
            for entry in self.getEntriesByX(i+1):
                value = " "
                if entry != None:
                    value = entry
                row_string += str(value)
                row_string += " | "
            print(row_string)
            print("_____________________________________")
        return ""
    
    # placeTiles is used to initialize the starting state into the current sudoku board, also updating the
    # domains of each tile accordingly as new tiles are inserted
    def placeTiles(self, startingState):
        for i in range(9):
            j = 0
            for tile in self.getByX(i+1):
                block = getBlockNum(i+1,j+1)
                if startingState[i][j] != 'e':
                    tile.entry = int(startingState[i][j])
                    # tile.domain = {}
                    self.forwardCheck(i+1, j+1, block, int(startingState[i][j]))
                else:
                    tile.entry = None
                j += 1

    # the following functions are used to get a row, column, or tile from the board
    def getByX(self, x) -> typing.List[Tile]:
        return [tile for tile in self.board if tile.x == x]

    def getEntriesByX(self,x) -> typing.List[int]:
        return [tile.entry for tile in self.board if tile.x == x]

    def getByY(self, y) -> typing.List[Tile]:
        return [tile for tile in self.board if tile.y == y]

    def getEntriesByY(self,y) -> typing.List[int]:
        return [tile.entry for tile in self.board if tile.y == y]

    def getByBlock(self, block) -> typing.List[Tile]:
        return [tile for tile in self.board if tile.block == block]

    def getEntriesByBlock(self, block) -> typing.List[int]:
        return [tile.entry for tile in self.board if tile.block == block]

    def isConflict(self,x,y,block,entry) -> bool:
        if entry in self.getEntriesByX(x):
            return True
        elif entry in self.getEntriesByY(y):
            return True
        elif entry in self.getEntriesByBlock(block):
            return True
        else:
            return False

    def getTile(self,position) -> Tile:
        query = [tile for tile in self.board if tile.x == position.row and tile.y == position.col]
        if len(query) == 1:
            return query[0]
        return None

    def forwardCheck(self,x,y,block,entry) -> bool:
        for (x,y,b) in zip(self.getByX(x),self.getByY(y),self.getByBlock(block)):
            x.updateDomain(entry)
            y.updateDomain(entry)
            b.updateDomain(entry)
            if x.domainEmpty() or y.domainEmpty() or b.domainEmpty():
                return False
        return True

    # Returns number of constraints that a given tile has on other unassigned variables.
    # Essentially, this is the number of unassigned variables other than itself in its row, column and block.
    def tileConstraintInvolvmentCount(self, tile_of_concern):
        count = 0
        # Check horizontal
        row = self.getByX(tile_of_concern.x)
        for tile in row:
            # Ensure not counting the tile of concern itself
            if tile is not tile_of_concern and tile.entry is None:
                count += 1
        # Check vertical
        column = self.getByY(tile_of_concern.y)
        for tile in column:
            # Ensure not counting the tile of concern itself
            if tile is not tile_of_concern and tile.entry is None:
                count += 1
        # Check block
        block = self.getByBlock(tile_of_concern.block)
        for tile in block:
            # Ensure not counting the tile of concern itself
            if tile is not tile_of_concern and tile.entry is None and tile.x != tile_of_concern.x and tile.y != tile_of_concern.y:
                count += 1
        return count

    def assignValueAt(self, position, value):
        global count
        tile = self.getTile(position)
        if count < 4:
            print("Variable %d at %d,%d | Entry: %d | Domain size: %d | Degree: %d" % (count + 1, position.row, position.col, value, len(tile.domain), self.tileConstraintInvolvmentCount(tile)))
            count +=1
        tile.entry = value
        # tile.domain = {}  # Domain should be empty now that it has been assigned


# Recursively solves the Sudoku problem.
# Returns a sovled board on success, None on failure.
def recursive_backtracking(board, depth):
    if board.unassigned == 0:
        return board
    tile = select_unassigned_tile(board)
    if tile is None:
        return board
    for value in order_domain_values(board, tile):
        new_board = assign_tile(board, tile.getPosition(), value)
        if new_board is not None:
            # print(new_board)
            # print("Depth: {}".format(depth))
            # print("Tile Domain: {}".format(tile.domain))
            # print("Assignment: {} at ({},{})".format(value, tile.getPosition().row, tile.getPosition().col))
            output = recursive_backtracking(new_board, depth+1) 
            if output is not None:
                return output

    return None


# Return the position of the tile to be selected for assignment next.
# Efficiently selects the next variable to be assigned based on minimum remaining values,
# and breaks ties with the degree heuristic.
def select_unassigned_tile(board):
    # Get a list of all the unassigned tiles in the board.
    unassigned = [tile for tile in board.board if tile.entry is None]
    if len(unassigned) == 0:
        return None
    # Determine best tile choice(s) based on fewest remaining values
    best_tile_choice_mrv = None
    for tile in unassigned:
        if best_tile_choice_mrv is None or len(tile.domain) < len(best_tile_choice_mrv[0].domain):
            best_tile_choice_mrv = [tile]
        elif len(tile.domain) == len(best_tile_choice_mrv[0].domain):
            best_tile_choice_mrv.append(tile)
    # Break tile ties with the degree heuristic
    best_tile_choice_deg = None
    best_degree_count = None
    for tile in best_tile_choice_mrv:
        tile_degree_count = board.tileConstraintInvolvmentCount(tile)
        if best_tile_choice_deg is None or tile_degree_count < best_degree_count:
            best_tile_choice_deg = [tile]
            best_degree_count = board.tileConstraintInvolvmentCount(best_tile_choice_deg[0])
        elif tile_degree_count == best_degree_count:
            best_tile_choice_deg.append(tile)
    # Break additional ties based on tile position (top left highest priority)
    best_tile_choice = None
    for tile in best_tile_choice_deg:
        if best_tile_choice is None or tile < best_tile_choice:
            best_tile_choice = tile
    return best_tile_choice


# Return a list of the domain values to be used for assigning
def order_domain_values(board, tile):
    return tile.domain


# Returns a new board with the tile at the given position set to the given value.
# The domains of various other variables are updated via forward checking.
# If forward checking finds a dead end, None is returned
def assign_tile(board, position, value):
    new_board = copy.deepcopy(board)
    new_board.assignValueAt(position, value)
    new_board.unassigned -= 1
    if new_board.forwardCheck(position.row, position.col, getBlockNum(position.row, position.col), value):
        return new_board
    return None


def main():
    # these are the starting states the sudoku puzzles, using 'e' characters for empty tiles
    startingState1 = [
        "ee1ee2eee",
        "ee5ee6e3e",
        "46eee5eee",
        "eee1e4eee",
        "6ee8ee143",
        "eeee9e5e8",
        "8eee49e5e",
        "1ee32eeee",
        "ee9eee3ee"
    ]
    startingState2 = [
        "ee5e1eeee",
        "ee2ee4e3e",
        "1e9eee2e6",
        "2eee3eeee",
        "e4eeee7ee",
        "5eeee7ee1",
        "eee6e3eee",
        "e6e1eeeee",
        "eeee7ee5e"
    ]
    startingState3 = [
        "67eeeeeee",
        "e25eeeeee",
        "e9e56e2ee",
        "3eee8e9ee",
        "eeeeee8e1",
        "eee47eeee",
        "ee86eee9e",
        "eeeeeee1e",
        "1e6e5ee7e"
    ]


    # a menu system is used to allow the user to select which sudoku starting state to solve from the 3 options
    print("\nWelcome to the sudoku solver.")
    while True:
        print("\nChoose a starting state to run:")
        print("  (A) 1")
        print("  (B) 2")
        print("  (C) 3")
        print("  (D) Quit")
        selection = input("Please enter a letter: ")
        global count
        count = 0
        
        if (selection == 'A' or selection == 'a' or selection == '1'):
            puzzle = Board(startingState1)
            start = time.time()
            print("\nFirst 4 States:")
            output = recursive_backtracking(puzzle, 0)
            end = time.time()
            print("\n\nSolved Sudoku for Starting State 1:")
            print(output)
            print('   Execution time => ' + str(end-start))
        elif (selection == 'B' or selection == 'b' or selection == '2'):
            puzzle = Board(startingState2)
            start = time.time()
            print("\nFirst 4 States:")
            output = recursive_backtracking(puzzle, 0)
            end = time.time()
            print("\n\nSolved Sudoku for Starting State 2:")
            print(output)
            print('   Execution time => ' + str(end-start))
        elif (selection == 'C' or selection == 'c' or selection == '3'):
            puzzle = Board(startingState3)
            start = time.time()
            print("\nFirst 4 States:")
            output = recursive_backtracking(puzzle, 0)
            end = time.time()
            print("\n\nSolved Sudoku for Starting State 3:")
            print(output)
            print('   Execution time => ' + str(end-start))
        elif (selection == 'D' or selection == 'd' or selection == 'Quit' or selection == 'quit'):
            print('\nExiting program...\n')
            break
        else:
            print("Invalid input: please enter a letter A-D (or a number 1-3).")


# Call to main
main()
