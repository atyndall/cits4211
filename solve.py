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
                    digit = int(char)
                    if digit >= 0 and digit <= 7:
                        pieces.append(digit)
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

def get_solution(input_file, width, buffer_size, utility_function, visualise):
    pieces = get_pieces_from_file(input_file)
    # builds the buffer
    buffer_size += 1
    piece_buffer = []
    if len(pieces) <= buffer_size:
        piece_buffer = pieces
        pieces = []
    else:
        piece_buffer = pieces[0:buffer_size]
        pieces = pieces[buffer_size:len(pieces)]
    #
    b = board.Board(width)
    #
    solution = []
    # empty sequences are false
    while piece_buffer:
        best_move = get_best_move(b, piece_buffer, utility_function)
        if visualise:
            print("best move:")
            best_move.print_rep_with_column()
            print("board before move:")
            b.print_grid()
            pass
        b.apply_move(best_move)
        if visualise:
            print("grid after move:")
            b.print_grid()
            print("-" * 20)
            pass
        solution.append(best_move)
        piece_buffer.remove(best_move.get_piece())
        if pieces:
            piece_buffer.append(pieces.pop(0))
    return solution
        
        
    
def test():
    s = get_solution("exampleinput.txt", 11, 1, utility.utility_function_a,
                     True)
