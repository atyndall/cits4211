from piece_definitions import pieces
import numpy as np
import sys
import collections
import itertools
import argparse
import multiprocessing
import time
from math import factorial
import cPickle as pickle

WIDTH = 4   # Default width
HEIGHT = 4  # Default height
PIECES = (WIDTH * HEIGHT) / 4 # Number of pieces that can fit in board
NOTIFY_INTERVAL = 10 # Number of seconds between progress notification
UNICODE = True # Unicode support is present in system

args = None

# Define a data structure to hold the piece information
class Piece(object):
  def __init__(self, ptype, rotation, h, w):
    object.__setattr__(self, 'ptype', ptype)
    object.__setattr__(self, 'roation', rotation)
    object.__setattr__(self, 'h', h)
    object.__setattr__(self, 'w', w)
    
  # Generates a unique representation of the piece based on its attributes.
  # Allows sorting of pieces in an appropriate way.
  def __hash__(self):
    h = "%d%d%d%d" % (self.ptype, self.rotation, self.h, self.w)
    return int(h)
    
  def __lt__(self, other):
    return self.__hash__() < other.__hash__()
    
  def __gt__(self, other):
    return self.__hash__() > other.__hash__()
    
  def __eq__(self, other):
    return self.__hash__() == other.__hash__()

# Same as Piece data structure, except that it has a "data" attribute that contains a
# matrix representing the piece's position on a HEIGHTxWIDTH plain.
# "data" attribute is very useful in performing calculations on pieces.
class DataPiece(Piece):
  def __init__(self, ptype, rotation, h, w):
    super(DataPiece, self).__init__(ptype, rotation, h, w)
    object.__setattr__(self, 'data', offset(get_piece(ptype, rotation), h, w) )
  
  # Make sure data matrix is always representative of data
  def __setattr__(self, name, value):
    if name == 'data':
      raise AttributeError, "Can't modify data, it is dynamically generated"
    object.__setattr__(self, name, value)
    object.__setattr__(self, 'data', offset(get_piece(self.ptype, self.rotation), self.h, self.w) )

  # Returns piece without representative matrix
  def get_dataless(self):
    return Piece(ptype=self.ptype, rotation=self.rotation, h=self.h, w=self.w)
    
#class DecisionNode(object):
#  def __init__(self, parent, values*):

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
    raise ValueError, "Shape with given offset cannot fit within dimensions"
  
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
  return np.rot90(pieces[type], rotation)
 
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
  for n, p in pieces.items():
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
      print_board(p)
       
      if not already:
        options.append((p, r))
     
    # Create all combinations
    for _, r in options:   
      for h in range(HEIGHT):
        for w in range(WIDTH):
          try:
            op = DataPiece(ptype=n, rotation=r, h=h, w=w)
            possibilities.append(op)
          except ValueError:
            pass

  lp = len(possibilities)
  print "There are %d possible orientations and positions for the given tetrominoes." % lp

  calculate_possible(possibilities)
 
# Check possibility
def check_possibility(pieces):
  board = np.zeros((HEIGHT, WIDTH), np.bool)
  donepieces = []
  for p in pieces:
    donepieces.append(p)
    if possible(p.data, board):
      board = np.logical_or(p.data, board)
    else:
      return None

  return pieces
 
# We combine all existing combinations and rotations of pieces to see which
# successfully fit together.
def calculate_possible(positions): 
  lp = len(positions)
  search_space = factorial(lp) / ( factorial(lp-PIECES) * factorial(PIECES) )
  
  print "Calculating possible combinations of tetrominoes from all placements (%d combinations)." % search_space

  combinations = []
  timer = time.time()
  pool = multiprocessing.Pool() # Use multiple processes to leaverage maximum processing power
  for i, res in enumerate( pool.imap_unordered(check_possibility, itertools.combinations(positions, PIECES), search_space/500) ):
    if res:
      combinations.append(res)
    if time.time() - timer > NOTIFY_INTERVAL: # If x seconds have elapsed
      print "Searched %d/%d placements (%.1f%% complete)" % (i, search_space, (i/float(search_space))*100)
      timer = time.time()
    
  lc = len(combinations)   
  print "There are %d possible combinations of %d tetrominoes within the %d positions." % (lc, PIECES, search_space)
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
  search_space = lp * factorial(PIECES)
  
  print "Calculating valid permutations of tetrominoes from all possible (%d permutations)." % search_space

  combinations = []
  timer = time.time()
  pool = multiprocessing.Pool() # Use multiple processes to leaverage maximum processing power
  for possibility in possibilities:
    # We permute every combination to work out the orders in which it would be valid
    for i, res in enumerate( pool.imap_unordered(check_validity, itertools.permutations(possibility, PIECES), search_space/20) ):
      if res:
        combinations.append((p.get_dataless() for p in res)) # We ditch the matricies as they are now unnecessary
        #combinations.append(res)
    if time.time() - timer > NOTIFY_INTERVAL: # If x seconds have elapsed
      print "Searched %d/%d placements (%.1f%% complete)" % (i, search_space, (i/float(search_space))*100)
      timer = time.time()
    
  lc = len(combinations)   
  print "There are %d valid permutations of %d tetrominoes within the %d possibilities." % (lc, PIECES, search_space)
  if args.out_v:
    pickle.dump(combinations, open(args.out_v,'wb'))
    print "Output saved to '%s'." % args.out_v
    
  combinations.sort()
  create_tree(combinations)
  
# Creates tree from sorted list of tuples of actions
def create_tree(permutations):
  return None
  
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
    
  args = parser.parse_args()

  WIDTH  = args.width   # Width of board
  HEIGHT = args.height  # Height of board
  
  if args.in_p:
    p = pickle.load( open(args.in_p,'rb') )
    calculate_valid(p)
  if args.in_v:
    p = pickle.load( open(args.in_v,'rb') )
    create_tree(p)
  else:
    calculate_positions()
