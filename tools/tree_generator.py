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

args = None

# Define a data structure to hold the piece information
NonHashPiece = collections.namedtuple('Piece', ['type', 'rotation', 'h', 'w', 'data'])
class OrientedPiece(NonHashPiece):
  def __hash__(self):
    h = "%d%d%d%d" % (self.type, self.rotation, self.h, self.w)
    return int(h)

# The print_board function prints out a representation of the [True, False]
# 2D-array as a set of HEIGHT*WIDTH empty and filled Unicode squares.
def print_board(a):
  for row in a:
    print(''.join([unichr(9632) if e else unichr(9633) for e in row]))

#
#   |
# ^ |
# h |
#   |
#   |____________
#        w >
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
# Tetris grid "a" would be permissable.
def possible(p, a):
  # See if the pieces clash
  land = np.logical_and(p, a)
  if np.any(land):
    return False
    
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
def calculate_possibilities():  
  print 'Computing all possible orientations and positions of given tetrominoes on %dx%d grid.' % (WIDTH, HEIGHT)
  possibilities = []
  for n, p in pieces.items():
    p_width = len(p[0])
    p_height = len(p)

    # Calculate the number of rotations a piece requires, default 3 (all)
    nrot = 4
    #if rall(p):
    #  if p_width == p_height: # Piece is square, no rotation needed
    #    nrot = 1
    #  else: # Piece is rectangular, one rotation needed
    #    nrot = 2

    for r in range(nrot):
      p = np.rot90(p, r)
      for h in range(HEIGHT):
        for w in range(WIDTH):
          try:
            op = OrientedPiece(type=n, rotation=r, h=h, w=w, data=offset(p, h, w))
            possibilities.append(op)
          except ValueError:
            pass

  lp = len(possibilities)
  print "There are %d possible orientations and positions for the given tetrominoes." % lp
  if args.out_p:
    pickle.dump(possibilities, open(args.out_p,'wb'))
    print "Output saved to '%s'." % args.out_p
  
  calculate_combinations(possibilities)
 
# Check possibility
def check_possibility(pieces):
  board = np.zeros((HEIGHT, WIDTH), np.bool)
  pos = True
  for p in pieces:
    if possible(p.data, board):
      board = np.logical_or(p.data, board)
    else:
      pos = False
      
  if pos:
    return pieces
 
# We permute over all possible combinations and rotations of pieces to see which
# successfully fit together.
def calculate_combinations(possibilities): 
  lp = len(possibilities)
  v_search_space = factorial(lp) / ( factorial(lp-PIECES) * factorial(PIECES) )
  
  print "Calculating valid combinations of tetrominoes from all placements (out of possible %d)." % v_search_space

  combinations = []
  pool = multiprocessing.Pool() # Use multiple processes to leaverage maximum processing power
  for i, res in enumerate( pool.imap_unordered(check_possibility, itertools.combinations(possibilities, PIECES)), v_search_space/500 ):
    if res: combinations.append(res)
    if i % (v_search_space/500) == 0 and i != 0:
      print "Searched %d/%d placements (%.1f%% complete)" % (i, v_search_space, (i/float(v_search_space))*100)
    
  lc = len(combinations)   
  print "There are %d valid combinations of %d tetrominoes within the %d possibilities." % (lc, PIECES, v_search_space)
  if args.out_c:
    pickle.dump(combinations, open(args.out_c,'wb'))
    print "Output saved to '%s'." % args.out_c
  
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
  pin.add_argument('--in-c', metavar='IN_C', type=str,
    help='import combinations and resume program')

  pout = parser.add_argument_group('output')
  pout.add_argument('--out-p', metavar='OUT_P', type=str,
    default='possibilities.p', help='save possibilities [default: possibilities.p]')
  pout.add_argument('--out-c', metavar='OUT_C', type=str,
    default='combinations.p', help='save combinations [default: combinations.p]')
    
  args = parser.parse_args()

  WIDTH  = args.width   # Width of board
  HEIGHT = args.height  # Height of board
  
  if args.in_c:
    c = pickle.load( open(args.in_c,'rb') )  
    for comb in c:
      for p in comb:
        print_board(p.data)
        print
      print '---'
    #calculate_pcombinations(c)
  elif args.in_p:
    p = pickle.load( open(args.in_p,'rb') )
    calculate_combinations(p)
  else:
    calculate_possibilities()
