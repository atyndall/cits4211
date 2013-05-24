# tree_generator was written with Python 2.7.4.
# The pickle files it produces should not be read with a version of
# Python less than 2.7.4, as they are not forwards compatible.
from piece_definitions import PIECES
import numpy as np
import sys
import collections
import itertools
import argparse
import multiprocessing
import time
import hashlib
from math import factorial
from rect import Rect
from tree import *
from helper import *
import cPickle as pickle

WIDTH = 4   # Default width
HEIGHT = 4  # Default height
BOARD = Board(HEIGHT, WIDTH)
PIECES_FIT = (WIDTH * HEIGHT) / 4 # Number of pieces that can fit in board
NUM_PIECES = len(PIECES)
NOTIFY_INTERVAL = 10 # Number of seconds between progress notification

args = None
  
# The adjacent function returns a 2D-array of all blocks that are vertically adjacent
# to the given 2D-array "a".
# A piece is not hovering in midair if part of it collides with the adjacent matrix.
def adjacent(a):
  HEIGHT = a.shape[0]
  WIDTH = a.shape[1]

  m = np.zeros((HEIGHT, WIDTH), np.bool)
  m[-1] = True # Set bottom row
  
  # Set edge values
  for x in range(HEIGHT):
    for y in range(WIDTH):
      if np.all(a[:, y]): # Special case for blocks that take up a whole column
        m[:, y] = False
      elif a[x, y] and x > 0:
        m[x-1, y] = True
        
  # Remove all but heighest values      
  for x in range(HEIGHT):
    for y in range(WIDTH):
      if m[x, y]:
        m[x+1:, y] = False
    
  return m
  
# The overhang function returns a 2D-array of all blocks that are empty space, but
# have a piece above them.
# A piece can be successfully dropped from above into its current position if it does
# not collide with the overhang matrix.
def overhang(a):
  HEIGHT = a.shape[0]
  WIDTH = a.shape[1]
  
  m = np.zeros((HEIGHT, WIDTH), np.bool)
  
  for y in range(WIDTH):
   for x in range(1, HEIGHT):
     if a[x-1, y] and not a[x, y]:
       m[x, y] = True
        
  return m
  
# The possible function returns a value indicating if a piece placement "p" on a given
# Tetris grid "a" would be possible (p does not occupy the same space as a).
def possible(p, a):
  # See if the pieces clash
  land = np.logical_and(p, a)
  if np.any(land):
    return False
  
  return True
 
# The possible function returns a value indicating if a piece placement "p" on a given
# Tetris grid "a" would be valid (p is not in mid-air, and can be dropped vertically
# into destination position).
def valid(p, a):
  # See if the piece is being placed in mid-air 
  hover = np.logical_and( p, adjacent(a) )
  if not np.any(hover):
    return False
    
  # See if the piece can be placed when dropped vertically
  drop = np.logical_and( p, overhang(a) )
  if np.any(drop):
    return False
    
  return True
  
# Calculate every possible position a piece can have on a WIDTH*HEIGHT grid
def calculate_positions():  
  print 'Computing all possible orientations and positions of given tetrominoes on %dx%d grid.' % (WIDTH, HEIGHT)
  possibilities = []
  for n, p in enumerate(PIECES):
    options = []
    p_width = len(p[0])
    p_height = len(p)

    # Calculate the number of rotations a piece requires, default 3 (all)
    nrot = 4
    if rall(p):
      if p_width == p_height: # Piece is square, no rotation needed
        nrot = 1
      else: # Piece is rectangular, one rotation needed
        nrot = 2
  
    # Add all rotations to an options list
    for r in range(nrot):
      p = np.rot90(p, r)
      
      # Remove duplicate rotations
      already = False
      for p2, r2 in options:
        if np.array_equal(p, p2):
          already = True
       
      if not already:
        options.append((p, r))
     
    # Create all combinations
    for _, r in options:   
      for h in range(HEIGHT):
        for w in range(WIDTH):
          try:
            op = DAction(BOARD, n, r, h, w)
            possibilities.append(op)
          except PieceNotFitError:
            pass

  lp = len(possibilities)
  print "There are %d possible orientations and positions for the given tetrominoes." % lp

  calculate_possible(possibilities)
 
# Check possibility
def check_possibility(cur_pieces):
  global PIECES
  board = np.zeros((HEIGHT, WIDTH), np.bool)

  indr = [] # List of coordinate pairs of all pieces
  lowestc = [HEIGHT, WIDTH] # Lowest coordinate of all pieces: (bottom, left)
  highestc = [0, 0] # Highest coordinate of all pieces: (top, right)
  
  boxcalc = False
  prev_p = None
  prev_bounding = None
  for p in cur_pieces:
    pheight = len(PIECES[p.piece])
    pwidth = len(PIECES[p.piece][0])
    coords = [[p.h, p.w], [pheight + p.h, pwidth + p.w]]
    max_bounding = Rect(lowestc, highestc)
    cur_bounding = Rect(*coords) # (bottom, left), (top, right)
    
    if prev_p is not None and prev_bounding is not None:
      board = np.logical_or(prev_p.data, board)
      indr.append(prev_bounding)
    
    prev_p = p
    prev_bounding = cur_bounding
    
    # We couldn't work out if it collides or not cheaply, so now onto the hard stuff
    if not possible(p.data, board):
      return None # This seems to have improved performance by like 10000%, very suspicious, keep an eye on it

  return cur_pieces
 
# Input seconds, output H:MM:SS
def time_output(s):
  hours, remainder = divmod(s, 3600)
  minutes, seconds = divmod(remainder, 60)
  return '%.f:%02.f:%02.f' % (hours, minutes, seconds)
 
# We combine all existing combinations and rotations of pieces to see which
# successfully fit together.
def calculate_possible(positions): 
  lp = len(positions)

  search_space = 0
  iterables = []
  for i in range(PIECES_FIT):
    search_space = search_space + ( factorial(lp) / ( factorial(lp-(PIECES_FIT-i)) * factorial(PIECES_FIT-i) ) )
    iterables.append(itertools.combinations(positions, PIECES_FIT-i))
  
  print "Calculating possible combinations of tetrominoes from all placements (%d combinations)." % search_space
  start_time = time.time()
  
  combinations = []
  timer = time.time()
  prev_i = 0

  pool = multiprocessing.Pool() # Use multiple processes to leaverage maximum processing power
  #for i, res in enumerate( itertools.imap(check_possibility, itertools.combinations(positions, PIECES_FIT)) ):
  for i, res in enumerate( pool.imap_unordered(check_possibility, itertools.chain(*iterables), max(5, search_space/500)) ):
    if res:
      combinations.append(res)
    elapsed = time.time() - timer
    if elapsed > NOTIFY_INTERVAL and i != 0: # If x seconds have elapsed
      pps = (i-prev_i)/elapsed
      print "Searched %d/%d placements (%.1f%% complete, %.0f pieces/sec, ~%s remaining)" % (i, search_space, (i/float(search_space))*100, pps, time_output((search_space-i)/pps))
      prev_i = i
      timer = time.time()
  pool.terminate()
    
  lc = len(combinations)   
  print "There are %d possible combinations of a maximum of %d tetrominoes within the %d positions." % (lc, PIECES_FIT, search_space)
  print "The calculation took %s." % time_output(time.time() - start_time)
  if args.out_p:
    pickle.dump(combinations, open(args.out_p,'wb'))
    print "Output saved to '%s'." % args.out_p
    
  calculate_valid(combinations)
    
# Check validity
def check_validity(pieces):
  board = np.zeros((HEIGHT, WIDTH), np.bool)
  pos = True  
  for p in pieces:
    if valid(p.data, board):
      board = np.logical_or(p.data, board)
    else:
      return None
  if pos:
    return pieces
   
# We permute over all possible combinations and rotations of pieces to see which
# are valid tetris plays.
def calculate_valid(possibilities): 
  lp = len(possibilities)
  search_space = lp * factorial(PIECES_FIT)
  start_time = time.time()
  
  print "Calculating valid permutations of tetrominoes from all possible (%d permutations)." % search_space

  combinations = []
  timer = time.time()
  prev_i = 0
  pool = multiprocessing.Pool() # Use multiple processes to leaverage maximum processing power
  for possibility in possibilities:
    # We permute every combination to work out the orders in which it would be valid
    for i, res in enumerate( pool.imap_unordered(check_validity, itertools.permutations(possibility, len(possibility)), max(5,search_space/20)) ):
      if res:
        combinations.append(res)
            
      elapsed = time.time() - timer
      if elapsed > NOTIFY_INTERVAL and i != 0: # If x seconds have elapsed
        pps = (i-prev_i)/elapsed
        print "Searched %d/%d placements (%.1f%% complete, %.0f pieces/sec, ~%s remaining)" % (i, search_space, (i/float(search_space))*100, pps, time_output((search_space-i)/pps))
        prev_i = i
        timer = time.time()
  pool.terminate()
    
  lc = len(combinations)   
  print "There are %d valid permutations of a maximum of %d tetrominoes within the %d possibilities." % (lc, PIECES_FIT, search_space)
  print "The calculation took %s." % time_output(time.time() - start_time)
  if args.out_v:
    pickle.dump(combinations, open(args.out_v,'wb'))
    print "Output saved to '%s'." % args.out_v
    
  # for c in combinations:
    # found = False
    # for e in c:
      # if e.piece in [5, 6] or found:
        # found = True
        # break
    # if found:
      # print_multi_board(to_byte_matrix(c))
      # print
    
  combinations.sort()
  create_tree(combinations)
  
# Creates tree from sorted list of tuples of actions
# "permutations" assumes a sorted list of permutations
def create_tree(permutations):
  print "Converting %d permutations into decision tree." % len(permutations)
  
  # Create root tree node. It has no parent and maximal utility.
  root = State(BOARD, None, np.zeros((HEIGHT,WIDTH), np.bool))
  root.utility = float('inf') # Utility of this action
  
  # Terminal nodes are used to reverse traverse the tree to calculate the max_utility
  term_nodes = []
  
  print "Calculating utilities."
  for nodes in permutations:
    actions = []
    parents = []
    children = []
    cur_parent = root
    board_state = np.zeros((HEIGHT,WIDTH), np.bool)
    for i, p in enumerate(nodes):
      board_state = np.logical_or(board_state, p.data)
      a = p.get_action()
      actions.append(a)
      
      if a not in cur_parent.actions[a.piece].keys(): # Make sure we don't override the state node
        s = State(BOARD, cur_parent, board_state)
        # print "%s{%s}.actions[%d][%s] = %s{%s}" % (cur_parent, hex(id(cur_parent)), a.piece, a, s, hex(id(s)))
        cur_parent.actions[a.piece][a] = s
        cur_parent = s
      else:
        cur_parent = cur_parent.actions[a.piece][a]
   
    # Get list of memory references when traversing downwards
    cur_state = root
    drilldown = []
    for a in actions:
      drilldown.append(id(cur_state))
      cur_state = cur_state.actions[a.piece][a]
    drilldown.append(id(cur_state))
    drilldown.reverse()
    
    # Get list of memory references when traversing upwards
    cur_state = cur_parent
    i = 0
    drillup = []
    while cur_state.parent is not None and i <= PIECES_FIT:
      drillup.append(id(cur_state))
      cur_state = cur_state.parent
      i += 1
    drillup.append(id(cur_state))
    
    # Sanity check to ensure that parent->children == children->parent
    if not (drillup == drilldown):
      print "Uh oh, something is wrong!"
      print drilldown
      print drillup
      print
    
    # cur_parent is the terminal node (at least currently)
    cur_parent.max_utility = cur_parent.utility # The maximum utility of a terminal node is itself
    term_nodes.append(cur_parent)
  
  # Reverse traverse the tree to calculate the max_utility
  print "Calculating max utilities."
  for n in term_nodes:
    i = 0
    while n.parent is not None:
      c = n
      n = n.parent
      
      if c.max_utility > n.max_utility:
        n.max_utility = c.max_utility
        
      i += 1
      if i > PIECES_FIT:
        break
        print "We seem to be stuck in a loop, exiting"
        
    if n != root:
      print "Something is very wrong. The final node isn't the parent."
        
  print "Tree created."
  if args.out_t:
    pickle.dump(root, open(args.out_t,'wb'))
    print "Output saved to '%s'." % args.out_t
  
  # Enter an interactive shell
  # import code
  # vars = globals().copy()
  # vars.update(locals())
  # shell = code.InteractiveConsole(vars)
  # shell.interact()
  
if __name__ == "__main__":
  parser = argparse.ArgumentParser(
    description='Computes a Tetris decision tree for a NxM sized grid'
  )

  parser.add_argument('--width', metavar='WIDTH', type=int,
    default=WIDTH, help='width of Tetris grid')
  parser.add_argument('--height', metavar='HEIGHT', type=int,
    default=HEIGHT, help='height of Tetris grid')

  pin = parser.add_mutually_exclusive_group()
  pin.add_argument('--in-p', metavar='IN_P', type=str,
    help='import possibilities and resume program')
  pin.add_argument('--in-v', metavar='IN_V', type=str,
    help='import valid permutations and resume program')

  pout = parser.add_argument_group('output')
  pout.add_argument('--out-p', metavar='OUT_P', type=str,
    default='possible.p', help='save possible combinations [default: possible.p]')
  pout.add_argument('--out-v', metavar='OUT_V', type=str,
    default='valid.p', help='save valid permutations [default: valid.p]')
  pout.add_argument('--out-t', metavar='OUT_T', type=str,
    default='tree.p', help='save generated tree [default: tree.p]')
    
  args = parser.parse_args()

  WIDTH  = args.width   # Width of board
  HEIGHT = args.height  # Height of board
  BOARD = Board(HEIGHT, WIDTH)
  PIECES_FIT = (WIDTH * HEIGHT) / 4
  
  if sys.version_info[:3] != (2, 7, 4):
    print "WARNING: This program was designed to work on Python 2.7.4."
    print "         Not using that version could cause pickle compatibility issues."
  
  if args.in_p:
    p = pickle.load( open(args.in_p,'rb') )
    calculate_valid(p)
  elif args.in_v:
    p = pickle.load( open(args.in_v,'rb') )
    create_tree(p)
  else:
    calculate_positions()
    
  print "Program complete."
