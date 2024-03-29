import sys
import copy

import move

# Defines the tetris game environment.
# Stores the game board using _grid, which contains a 2d list.
# Rows and columns can be accessed like this _grid[row][column]
# _grid stores rows starting at the bottom, going up, cols left to right.
# Each grid spot is a boolean, containing True if there is a block there,
# otherwise false.
# _grid only stores enough rows to contain the row with the highest block.
# Consequently an empty grid will have 0 rows, and a grid with only an
# O block (square block) will have 2 rows
# The function place_block will generate new rows when needed
class Board:
    def __init__(self, width):
        self._width = width
        self._grid = []
        self._rows_cleared = 0

    def copy(self):
        return copy.deepcopy(self)

    def get_width(self):
        return self._width

    def get_num_rows(self):
        return len(self._grid)
        
    def get_rows_cleared(self):
        return self._rows_cleared
      
    def get_num_holes(self):
        n = 0
        for row in reversed(self._grid):
            for column in row:
                if not column:
                    n += 1
        return n

    # Places a block at the indicated row and column
    # Will generate new rows if needed
    def place_block(self, row, column):
        # Adds extra rows if necessary
        diff =  row - len(self._grid) + 1
        if diff > 0:
            for i in range(0, diff):
                self.append_row()
                
        if column >= self._width:
            raise Exception("column given is larger than width")
        if self._grid[row][column] == True:
            raise Exception("block already at position")
        
        self._grid[row][column] = True

    def block_at(self, row, column):
        if column >= self._width:
            raise Exception("column given is larger than width")
        if row < len(self._grid):
            return self._grid[row][column]
        else:
            return False

    def on_board(self, row, column):
        return row >= 0 and column >= 0 and column < self._width

    def is_wall(self, column):
        return column == -1 or column == self._width

    def is_floor(self, row):
        return row == -1

    def append_row(self):
        self._grid.append([False]*self._width)

    def remove_full_lines(self):
        full_lines = []
        for i in range(0, len(self._grid)):
            if all(self._grid[i]):
                full_lines.append(i)
        for line in reversed(full_lines):
            self._grid.pop(line)
            self._rows_cleared += 1

    # Checks if the piece can be placed on the board with its column.
    # Changes the column to a valid one if it can.
    # Returns True if afterwards, the piece can be placed on the wall.
    def move_column_valid(self, move):
        if move.get_column() < 0:
            return false
        # if the piece goes past the right wall
        if move.get_column() + move.get_width() > self._width:
            new_value = self._width - move.get_width()
            # if the board width is so low the piece still doesn't fit
            if new_value < 0:
                return false
            move.set_column(new_value)
        return True

    # Helper function for apply_move
    def collision_at_row(self, move, board_row):
        for row in range(0, move.get_height()):
            for column in range(0, move.get_width()):
                if move.block_at(row, column):
                    if self.block_at(board_row + row,
                                     column + move.get_column()):
                        return True
        return False

    # Helper function for apply_move
    def place_piece_at_row(self, move, board_row):
        for row in range(0, move.get_height()):
            for column in range (0, move.get_width()):
                if move.block_at(row, column):
                    self.place_block(board_row + row,
                                     move.get_column() + column)

    def apply_move(self, move):
        if not self.move_column_valid(move):
            raise Exception("Move column not valid, unable to get valid value")
        # Loops from top row to the bottom row until a row with a collision
        # is found. The piece is then placed on the row it. If no such row
        # is found, the piece is placed on row 0
        for board_row in reversed(range(0, self.get_num_rows())):
            if self.collision_at_row(move, board_row):
                self.place_piece_at_row(move, board_row + 1)
                self.remove_full_lines()
                return
        self.place_piece_at_row(move, 0)
        self.remove_full_lines()

    # makes a copy of the board, applies the move to it, then returns the copy
    def apply_move_copy(self, move):
        cp = self.copy()
        cp.apply_move(move)
        return cp

    def print_grid(self):
        for row in reversed(self._grid):
            sys.stdout.write("|")
            for column in row:
                if column:
                    sys.stdout.write("X")
                else:
                    sys.stdout.write(" ")
                sys.stdout.write("|")
            sys.stdout.write("\n")
        sys.stdout.write("\n")

    

def test():
    b = Board(11)
    b.apply_move(move.Move(1, 1, 0))
    b.apply_move(move.Move(1, 1, 4))
    b.apply_move(move.Move(4, 1, 8))
    
    b.apply_move(move.Move(1, 1, 4))
    b.apply_move(move.Move(1, 1, 4))
    b.apply_move(move.Move(1, 1, 4))
    b.apply_move(move.Move(1, 1, 4))
    b.apply_move(move.Move(1, 1, 2))
    b.print_grid()
    b.apply_move(move.Move(1, 1, 0))
    b.apply_move(move.Move(1, 1, 7))
    b.apply_move(move.Move(3, 3, 5))
    b.apply_move(move.Move(3, 3, 3))
    b.apply_move(move.Move(3, 1, 8))
    b.print_grid()
