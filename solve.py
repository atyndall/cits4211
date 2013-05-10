import copy
import sys

import board
import move
import utility

def get_pieces_from_file(filename):
    pieces = []
    with open(filename, "r") as f:
        for line in f:
            for char in line:
                if char.isdigit():
                    pieces.append(int(char))
                else:
                    # skip rest of this line
                    break
    return pieces

def write_solution_to_file(solution, filename):
    with open(filename, "w") as f:
        for m in solution:
            f.write("{0} {1} {2}\n".format(m.get_piece(), m.get_rotation(),
                                      m.get_column()))

def get_best_move(board, pieces, utility_function):
    best_move = None
    best_utility = -100000
    for piece in pieces:
        for rotation in range(0, 4):
            for column in range(0, board.get_width()):
                m = move.Move(piece, rotation, column)
                if board.move_column_valid(m):
                    b = board.apply_move_copy(m)
                    utility = utility_function(b)
                    if utility > best_utility:
                        best_move = m
                        best_utility = utility
    return best_move


b = board.Board(11)
b.apply_move(move.Move(1, 1, 0))
c = copy.deepcopy(b)
b.apply_move(move.Move(1, 1, 0))
b.print_grid()
c.print_grid()

print("-------------------")

pieces = (2, 3, 4, 5, 6, 7)
b = board.Board(11)
m = get_best_move(b, pieces, utility.utility_function_a)
b.apply_move(m)
b.print_grid()

pieces = (3, 4, 5, 6, 7)
m = get_best_move(b, pieces, utility.utility_function_a)
b.apply_move(m)
b.print_grid()

print("-------------------")

p = get_pieces_from_file("exampleinput.txt")

solution = [move.Move(1, 1, 0), move.Move(3, 0, 2), move.Move(5, 1, 4)]
write_solution_to_file(solution, "output.txt")
