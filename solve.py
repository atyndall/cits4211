import copy
import sys
import random
import operator
import pickle
import argparse
import numpy as np
import sys
import time
import os

import board
import move
import utility
from tools.tree import *
import tools.piece_definitions

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

def get_solution(pieces, width, buffer_size, utility_function, visualise):
    #pieces = get_pieces_from_file(input_file)
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
    return (b, solution)

def get_solution_height(solution, width):
    b = board.Board(width)
    for move in solution:
        b.apply_move(move)
    return b.get_num_rows()

def get_solution_max_height(solution, width):
    b = board.Board(width)
    max_height = 0
    for move in solution:
        b.apply_move(move)
        if b.get_num_rows() > max_height:
            max_height = b.get_num_rows()
    return max_height

def print_solution_board(solution, width):
    b = board.Board(width)
    for move in solution:
        b.apply_move(move)
    b.print_grid()

def get_random_pieces(seed, num_piece_groups, num_pieces_per_groud):
    random.seed(seed)
    pieces = []
    for i in range(0, num_piece_groups):
        piece_set = []
        for j in range(0, num_pieces_per_groud):
            piece_set.append(random.randint(1, 7))
        pieces.append(piece_set)
    return pieces

def review(seed, num_tests, num_pieces_per_test, width, buffer_size, args):
    pieces = get_random_pieces(seed, num_tests, num_pieces_per_test)
    height_dictionary = {}
    max_height_dictionary = {}
    for a in args[0]:
        for b in args[1]:
            for c in args[2]:
                for d in args[3]:
                    for e in args[4]:
                        function = utility.variable_alpha(a, b, c, d, e)
                        height = 0.0
                        max_height = 0.0
                        for piece_set in pieces:
                            solution = get_solution(piece_set, width,
                                                    buffer_size, function,
                                                    False)
                            height += get_solution_height(solution, width)
                            max_height += get_solution_max_height(solution,
                                                                  width)
                        height /= num_tests
                        max_height /= num_tests
                        height_dictionary[(a, b, d, c, e)] = height
                        max_height_dictionary[(a, b, d, c, e)] = max_height
                        print((a, b, c, d, e), height, max_height)
    #
    sorted_hd = sorted(height_dictionary.iteritems(), key=operator.itemgetter(1))
    sorted_mhd = sorted(max_height_dictionary.iteritems(),
                        key=operator.itemgetter(1))
    print("Best 10 height:")
    for item in sorted_hd[0:10]:
        h = height_dictionary[item[0]]
        mh = max_height_dictionary[item[0]]
        print("{0} height: {1} max height: {2}".format(item[0], h, mh))
    print("Best 10 max height:")
    for item in sorted_mhd[0:10]:
        h = height_dictionary[item[0]]
        mh = max_height_dictionary[item[0]]
        print("{0} height: {1} max height: {2}".format(item[0], h, mh))

def get_tree2():
    path = 'trees/tree2.p'
    if sys.platform.startswith('win32'):
        path = 'trees/tree2_win.p'
    if not hasattr(get_tree2, "t"):
        get_tree2.t = pickle.load(open(path, 'rb'))
        get_tree2.t.utility = 0
    return copy.copy(get_tree2.t)        
        
def get_tree3():
    path = 'trees/tree3.p'
    if sys.platform.startswith('win32'):
        path = 'trees/tree3_win.p'
    if not hasattr(get_tree3, "t"):
        get_tree3.t = pickle.load(open(path, 'rb'))
        get_tree3.t.utility = 0
    return copy.copy(get_tree3.t)

def get_tree4():
    path = 'trees/tree4.p'
    if sys.platform.startswith('win32'):
        path = 'trees/tree4_win.p'
    if not hasattr(get_tree4, "t"):
        get_tree4.t = pickle.load(open(path, 'rb'))
        get_tree4.t.utility = 0
    return copy.copy(get_tree4.t)

def load_trees(width):
    sys.path.append("tools")
    trees = []
    if width < 3:
        raise Exception("Width is smaller than 3")
    elif width == 3:
        return [get_tree3()]
    elif width == 4:
        return [get_tree4()]
    elif width == 5:
        return [get_tree2(), get_tree3()]
    elif width == 6:
        return [get_tree3, get_tree3()]
    elif width == 7:
        return [get_tree4(), get_tree3()]
    elif width == 8:
        return [get_tree4(), get_tree4()]
    elif width == 9:
        return [get_tree3(), get_tree3(), get_tree3()]
    else:
        return load_trees(width - 4) + [get_tree4()]
    
def tree_get_best_action(trees, times_filled, pieces):
    best_action = None
    best_utility = None
    for i in range(0, len(trees)):
        tree = trees[i]
        for piece in pieces:
            for action in tree.actions[piece - 1]:
                state = tree.actions[piece - 1][action]
                u = state.max_utility #- (times_filled[i] * 1000)
                if best_utility == None or best_utility < u:
                    best_utility = u
                    best_action = (i, action)
                # if 2 trees best action have a max utility of inf, makes sure
                # the tree that has been filled less is selected
                elif best_utility == u == float('inf') and \
                times_filled[i] < times_filled[best_action[0]]:
                    best_utility = u
                    best_action = (i, action)
    # print best_utility
    return best_action

def tree_get_solution(pieces, width, buffer_size, visualise):
    b = board.Board(width)
    trees = load_trees(width)
    times_filled = [0, 0, 0] # stores how many times each tree has been replaced
    buffer_size += 1
    piece_buffer = []
    if len(pieces) <= buffer_size:
        piece_buffer = pieces
        pieces = []
    else:
        piece_buffer = pieces[0:buffer_size]
        pieces = pieces[buffer_size:len(pieces)]
    solution = []
    # Each loop, the best action is found and applied, the used piece is removed
    # from piece_buffer, the next piece is placed, and the best action is
    # converted into a Move object and added to solution
    while piece_buffer:
        # print piece_buffer
        
        a = tree_get_best_action(trees, times_filled, piece_buffer)
        if a == None:
            # print("Best action returned is none, adding more trees")
            for i in range(0, len(trees)):
                tree = trees[i]
                # print "Trees[{0}] is being replaced".format(i)
                times_filled[i] += 1
                # print times_filled
                if tree.board._width == 3:
                    trees[i] = get_tree3()
                elif tree.board._width == 4:
                    trees[i] = get_tree4()
                elif tree.board._width == 2:
                        trees[i] = get_tree2()
            continue
        best_action = a[1]
        a_tree = a[0]
        
        # print str(best_action) + " " + str(a_tree)
        # Applies move to try
        trees[a_tree] = trees[a_tree].actions[best_action.piece][best_action]
        # for tree in trees:
            # print_board(tree._board_state)
            # print("")
        # print("==============================")
        # Add move to solution
        column = best_action.w
        for i in range(0, a_tree):
            column += trees[i].board._width
        
        m = move.Move(best_action.piece + 1, best_action.rotation, column)
        
        if visualise:
            print("best move:")
            m.print_rep_with_column()
            print("board before move:")
            b.print_grid()
            pass
        
        solution.append(m)
        b.apply_move(m)
        
        if visualise:
            print("grid after move:")
            b.print_grid()
            print("-" * 20)
            pass

        
        #
        piece_buffer.remove(best_action.piece + 1)
        if pieces:
            piece_buffer.append(pieces.pop(0))
        # if tree is complete, replace it with a fresh one
        for i in range(0, len(trees)):
            tree = trees[i]
            if np.all(tree._board_state):
                print "Trees[{0}] is full, replacing it".format(i)
                times_filled[i] += 1
                print times_filled
                if tree.board._width == 3:
                    trees[i] = get_tree3()
                elif tree.board._width == 4:
                    trees[i] = get_tree4()
                elif tree.board._width == 2:
                    trees[i] = get_tree2()
    return (b, solution)

def tree_search(trees, piece_buffer, pieces, a=0):
    #print a
    for i in range(0, len(trees)):
        tree = trees[i]
        for piece in piece_buffer:
            for action in tree.actions[piece - 1]:
                state = tree.actions[piece - 1][action]
                if state.max_utility == float("inf"):
                    nt = copy.copy(trees)
                    nt[i] = state
                    npb = copy.copy(piece_buffer)
                    np = copy.copy(pieces)
                    npb.remove(action.piece + 1)
                    if np:
                        npb.append(np.pop(0))
                    #print nt
                    # if all trees are filled
                    if all(t.utility == float("inf") for t in nt):
                        #print [action]
                        return [(i, action)]
                    #
                    r = tree_search(nt, npb, np, a+1)
                    #print "r:"
                    #print r
                    #if r is not empty or == None
                    if r != None and len(r) != 0:
                        r.append((i, action))
                        #print r
                        return r
    return None

def tree_search_get_solution(pieces, width, buffer_size, visualize):
    print pieces
    b = board.Board(width) # Init a board so we can keep better track of the state
    trees = load_trees(width)
    buffer_size += 1
    piece_buffer = []
    if len(pieces) <= buffer_size:
        piece_buffer = pieces
        pieces = []
    else:
        piece_buffer = pieces[0:buffer_size]
        pieces = pieces[buffer_size:len(pieces)]
    solution = []
    s = tree_search(trees, piece_buffer, pieces)
    if s == None:
        print "s == None, no optimal solution found"
    s.reverse()
    for i, action in s:
        column = action.w
        for i in range(0, i):
            column += trees[i].board._width
        m = move.Move(action.piece + 1, action.rotation, column)
        
        if visualise:
            print("best move:")
            m.print_rep_with_column()
            print("board before move:")
            b.print_grid()
            pass
        
        b.apply_move(apply_move)
        
        if visualise:
            print("grid after move:")
            b.print_grid()
            print("-" * 20)
            pass
        
        solution.append(m)
        # TODO: remove used piece form buffer and add next piece
        piece_buffer.remove(action.piece + 1)
        if pieces:
            piece_buffer.append(pieces.pop(0))
    print piece_buffer
    print pieces
    return (b, solution)
                    

def test():
    #review(1, 2, 10, 11, 1,
    #       ((-40, -60, -80, -160), (-40, -60, -80, -160), (1, 2, 4),
    #        (1, 2, 4), (1, 2, 4)))
    #return
    #s = get_solution(get_random_pieces(112312312, 1, 1000)[0], 11, 1,
    #                 utility.variable_alpha(-100, -80, 10, 3, 1), False)
    s = get_solution(get_pieces_from_file("exampleinput.txt"), 11, 1,
                     utility.variable_alpha(-100, -80, 10, 3, 1), True)
    print(get_solution_height(s, 11))
    print(get_solution_max_height(s, 11))
    print_solution_board(s, 11)

# tree test
def tt():
    #s = tree_search_get_solution([5,2,5,1,4,6,3,3,5,6,4, 7, 7, 7], 11, 1)
    s = tree_search_get_solution(get_random_pieces(None, 1, 15)[0], 11, 1)
    #s = tree_get_solution(get_random_pieces(198, 1, 30)[0], 11, 1)
    print(get_solution_height(s, 11))
    print(get_solution_max_height(s, 11))
    print_solution_board(s, 11)
    
def out_stats(file, input, width, buffersize, method, rows_cleared, final_height, num_holes):
    print
    print "STATS"
    print "Rows cleared: %d" % rows_cleared
    print "Final height: %d" % final_height
    print "Number of holes: %d" % num_holes

    exists = os.path.exists(file)
    with open(file, 'a') as f:
      if not exists:
        f.write("curtime,input,width,buffersize,method,rows_cleared,final_height,num_holes\n")
      f.write("%d,%s,%d,%d,%d,%d,%d,%d\n" % (int(round(time.time() * 1000)), input, width, buffersize, method, rows_cleared, final_height, num_holes))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Tetris AI program')

    parser.add_argument('--method', metavar='METHOD', type=int,
                        default=0,
                        help='Method to use, 0:none, 1:Utility, 2:Tree')
    parser.add_argument('--input', metavar='INPUT', default="input.txt",
                        help="Input file")
    parser.add_argument('--output', metavar='OUTPUT', default="output.txt",
                        help="Output file")
    parser.add_argument('--width', metavar='WIDTH', type=int, default=11,
                        help="The width of the board")
    parser.add_argument('--buffer-size', metavar='BUFFER-SIZE', type=int,
                        default=1, help="The buffer size")
    parser.add_argument('--visualise', metavar='VISUALISE', type=bool,
                        default=False, help="Whether to visualise the program")
    parser.add_argument('--stats-out', metavar='STATS-OUT', default="stats.csv",
                        help="Output stats CSV file")
                        
    args = parser.parse_args()
    
    rows_cleared = 0
    final_height = 0
    num_holes = 0
    
    if args.method == 1:
        b, s = get_solution(get_pieces_from_file(args.input), args.width,
                         args.buffer_size,
                         utility.variable_alpha(-100, -80, 10, 3, 1),
                         args.visualise)
        write_solution_to_file(s, args.output)
        
        rows_cleared = b.get_rows_cleared()
        final_height = b.get_num_rows()
        num_holes = b.get_num_holes()
    elif args.method == 2:
        b, s = tree_get_solution(get_pieces_from_file(args.input), args.width,
                          args.buffer_size, args.visualise)
        write_solution_to_file(s, args.output)
        
        rows_cleared = b.get_rows_cleared()
        final_height = b.get_num_rows()
        num_holes = b.get_num_holes()
        
    if args.stats_out:
      out_stats(args.stats_out, args.input, args.width, args.buffer_size, args.method, rows_cleared, final_height, num_holes)
    
    
