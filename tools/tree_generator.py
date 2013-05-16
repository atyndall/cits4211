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
import cPickle as pickle

WIDTH = 4   # Default width
HEIGHT = 4  # Default height
PIECES_FIT = (WIDTH * HEIGHT) / 4 # Number of pieces that can fit in board
NUM_PIECES = len(PIECES)
NOTIFY_INTERVAL = 10 # Number of seconds between progress notification
UNICODE = True # Unicode support is present in system

args = None
    
# Action represents an action
class Action(object):
  def __init__(self, piece, rotation, h, w):
    if not (isinstance(piece, int) and isinstance(rotation, int)
      and isinstance(h, int) and isinstance(w, int)):
      raise ValueError, "Incorrect parameters"
  
    self.piece = piece
    self.rotation = rotation
    self.h = h
    self.w = w
    
  def __repr__(self):
    return "A(p:%s r:%s h:%s w:%s)" % (self.piece, self.rotation, self.h, self.w)
    
  # Generates a unique representation of the piece based on its attributes.
  # Allows sorting of pieces in an appropriate way.
  def __hash__(self):
    h = "%d%d%d%d" % (self.piece, self.rotation, self.h, self.w)
    return int(h)
    
  def __lt__(self, other):
    return self.__hash__() < other.__hash__()
    
  def __gt__(self, other):
    return self.__hash__() > other.__hash__()
    
  def __eq__(self, other):
    return self.__hash__() == other.__hash__()
    
  def __hash__(self):
    h = "%d%d%d%d" % (self.piece, self.rotation, self.h, self.w)
    return int(h) 
 
# Same as Action data structure, except that it has a "data" attribute that contains a
# matrix representing the piece's position on a HEIGHTxWIDTH plain.
# "data" attribute is very useful in performing calculations on pieces.
class DAction(Action):
  def __init__(self, piece, rotation, h, w):
    super(DAction, self).__init__(piece, rotation, h, w)
    self.data = offset(get_piece(piece, rotation), h, w)

  # Returns piece without representative matrix
  def get_action(self):
    return Action(self.piece, self.rotation, self.h, self.w)
    
  def __repr__(self):
    return "DA(p:%s r:%s h:%s w:%s)" % (self.piece, self.rotation, self.h, self.w)
  
# State represents a current state of the game
class State(object):
  def __init__(self, parent, board):
    self.actions = [dict() for x in range(NUM_PIECES)] # Actions are indexes to new states, indexed by piece for performance
    self.parent = parent
    # self.board = board # NumPy matrix representing board at given time
    self.utility = utility(board) # Utility of this state
    self._bhash = matrix_hash(board) # Stores unique representation of state

  def __repr__(self):
    return "S(%s, u:%.2f)" % (hex(self.__hash__())[2:-1], self.utility)

  def __hash__(self):
    s = "%d%d" %(id(self.parent), self._bhash)
    return int(s)
    
# Returns a unique hash for each matrix' dimensions
# Hash is only unique for matricies of the same dimension
def matrix_hash(x):
  return long(''.join(['1' if e else '0' for e in np.reshape(x, -1)]), 2)

# Returns the utility of the board in its current state
def utility(board):
  return float('-inf')
      
# The print_board function prints out a representation of the [True, False]
# 2D-array as a set of HEIGHT*WIDTH empty and filled Unicode squares (or ASCII if there is no support).
def print_board(a):
  global UNICODE
  for row in a:
    if UNICODE:
      try:
        print(''.join([unichr(9632) if e else unichr(9633) for e in row]))
        continue
      except UnicodeEncodeError: # Windows compatibility
        UNICODE = False

    print(''.join(['#' if e else '0' for e in row])) 

# Error raised when offset function cannot fit piece in
class PieceNotFitError(ValueError):
  pass
    
#
#   |
# ^ |
# h |
#   |
#   |____________
#  0     w >
#
# The offset function attempts to place a smaller 2D-array "a" in a HEIGHT*WIDTH
# sized 2D-array with offsets of "h" and "w" as per the diagram above.
def offset(a, h, w):
  a_height = a.shape[0]
  a_width = a.shape[1]

  if (a_height + h) > HEIGHT or (a_width + w) > WIDTH:
    raise PieceNotFitError, "Shape with given offset cannot fit within dimensions"
  
  rows = []
  
  start_height = HEIGHT - (h + a_height)
  end_height = start_height + a_height
  
  for i in range(HEIGHT):
    if i >= start_height and i < end_height:
      rows.append([False]*w + list(a[i - start_height]) + [False]*(WIDTH - w - a_width))
    else:
      rows.append([False]*WIDTH)
      
  return np.array(rows)
  
# The get_piece function returns an piece with the appropriate rotation
def get_piece(type, rotation):
  return np.rot90(PIECES[type], rotation)
 
# The rall function recursively checks that all lists and sublists of element "a"
# have a True value, otherwise it returns False. 
def rall(a):
  for i in a:
    if isinstance(i, collections.Iterable):
      if not rall(i):
        return False 
    elif not i:
      return False
      
  return True
  
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
            op = DAction(n, r, h, w)
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
  search_space = factorial(lp) / ( factorial(lp-PIECES_FIT) * factorial(PIECES_FIT) )
  
  print "Calculating possible combinations of tetrominoes from all placements (%d combinations)." % search_space
  start_time = time.time()
  
  combinations = []
  timer = time.time()
  prev_i = 0
  pool = multiprocessing.Pool() # Use multiple processes to leaverage maximum processing power
  #for i, res in enumerate( itertools.imap(check_possibility, itertools.combinations(positions, PIECES_FIT)) ):
  for i, res in enumerate( pool.imap_unordered(check_possibility, itertools.combinations(positions, PIECES_FIT), max(5, search_space/500)) ):
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
  print "There are %d possible combinations of %d tetrominoes within the %d positions." % (lc, PIECES_FIT, search_space)
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
    for i, res in enumerate( pool.imap_unordered(check_validity, itertools.permutations(possibility, PIECES_FIT), max(5,search_space/20)) ):
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
  print "There are %d valid permutations of %d tetrominoes within the %d possibilities." % (lc, PIECES_FIT, search_space)
  print "The calculation took %s." % time_output(time.time() - start_time)
  if args.out_v:
    pickle.dump(combinations, open(args.out_v,'wb'))
    print "Output saved to '%s'." % args.out_v
    
  combinations.sort()
  create_tree(combinations)
  
# Creates tree from sorted list of tuples of actions
# "permutations" assumes a sorted list of permutations
def create_tree(permutations):
  print "Converting %d permutations into decision tree." % len(permutations)
  
  # Create root tree node. It has no parent and maximal utility.
  root = State(None, np.zeros((HEIGHT,WIDTH), np.bool))
  root.utility = float('inf') # Utility of this action
  
  for nodes in permutations:
    cur_parent = root
    board = np.zeros((HEIGHT,WIDTH), np.bool)
    for p in nodes:
      board = np.logical_or(board, p.data)
      s = State(cur_parent, board)
      a = p.get_action()
      
      cur_parent.actions[a.piece][a] = s
      cur_parent = s
   
  print "Tree created."
  if args.out_t:
    pickle.dump(combinations, open(args.out_t,'wb'))
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
  PIECES_FIT = (WIDTH * HEIGHT) / 4
  
  if args.in_p:
    p = pickle.load( open(args.in_p,'rb') )
    calculate_valid(p)
  elif args.in_v:
    p = pickle.load( open(args.in_v,'rb') )
    create_tree(p)
  else:
    calculate_positions()
