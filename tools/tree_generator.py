from piece_definitions import pieces
import numpy as np
import sys
import collections
import itertools
import argparse
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
# If "floor" is set to True, the bottom row of the matrix will also be set to True.
def adjacent(a, floor=False):
  HEIGHT = a.shape[0]
  WIDTH = a.shape[1]

  m = np.zeros((HEIGHT, WIDTH), np.bool)
  
  if floor:
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

# The simulate_drop function will transform "piece" from where it sits as an overlay
# on "board" to see if it collides with anything on "board".  
def simulate_drop(board, piece):
  a = get_piece(piece.type, piece.rotation)
  for h in range(piece.h, HEIGHT):
    try:
      off = offset(a, h, piece.w)
      r = np.logical_or(board, off)
      if np.any(r):
        return False
    except ValueError:
      pass
      
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
    if rall(p):
      if p_width == p_height: # Piece is square, no rotation needed
        nrot = 1
      else: # Piece is rectangular, one rotation needed
        nrot = 2

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
 
# We permute over all possible combinations and rotations of pieces to see which
# successfully fit together.
def calculate_combinations(possibilities): 
  lp = len(possibilities)
  print "Calculating valid combinations of tetrominoes from all placements."
  v_search_space = factorial(lp) / ( factorial(lp-PIECES) * factorial(PIECES) )
  combinations = []
  i = 0
  for i, en in enumerate( itertools.combinations(possibilities, PIECES) ):
    a, b, c, d = en
    first = np.logical_and(a.data, b.data)
    
    # If there is no tetromino collision, the result of the logical AND should be a completely
    # False 2D-array
    if not np.any(first):
      ab = np.logical_or(a.data, b.data)
      second = np.logical_and(ab, c.data)
      
      if not np.any(second):
        abc = np.logical_or(ab, c.data)
        third = np.logical_and(abc, d.data)
        
        if not np.any(third):
          combinations.append((a,b,c,d))     

    if i % (v_search_space/250) == 0 and i != 0: # Output a message every now and then with progress
      print "Searched %d/%d placements (%.1f%% complete)" % (i, v_search_space, (i/float(v_search_space))*100)
     
  lc = len(combinations)   
  print "There are %d valid combinations of %d tetrominoes within the %d possibilities." % (lc, PIECES, v_search_space)
  if args.out_c:
    pickle.dump(combinations, open(args.out_c,'wb'))
    print "Output saved to '%s'." % args.out_c
  
  calculate_pcombinations(combinations)

# We must exclude combinations that are not possible when "dropping" the pieces from above.
def calculate_pcombinations(combinations):
  print "Calculating possible orders of placement and excluding impossible orderings."

  lc = len(combinations) 
  p_search_space = factorial(lc) / factorial(lc-PIECES)
  pcombinations = []
  for combination in combinations:
    for pieces in itertools.permutations(combination):
      board = np.zeros((HEIGHT,WIDTH), np.bool)
      for piece in pieces:
        if simulate_drop(board, piece):
          board = np.logical_and(board, piece.data)
        else:
          continue
      
      for p in pieces:
        print_board(p.data)
        print
      print '---'
      
      pcombinations.append(pieces)
       
      # # print_board(a.data)
      # # print
      # # print_board(b.data)
      # # print
      # # print_board(adjacent(a.data, floor=True))
      # # print
      # # print_board(np.logical_and(b.data, adjacent(a.data, floor=True)))
      # # print '--'
      
      # # TODO: adjacent currently cannot handle some edge cases
      
      # # If b does not sit on a or the floor
      # first = np.logical_and(b.data, adjacent(a.data, floor=True))
      # if not np.any(first):
        # continue
        
      # # If c does not sit on a, b or the floor
      # ab = np.logical_or(a.data, b.data)
      # second = np.logical_and(c.data, adjacent(ab, floor=True))
      # if not np.any(second):
        # continue
      
      # # If d does not sit a, b, c or the floor
      # abc = np.logical_or(ab, c.data)
      # third = np.logical_and(d.data, adjacent(abc, floor=True))
      # if not np.any(third):
        # continue
        
      # If we're still here, that means we've got a valid placement
      #pcombinations.append((a,b,c,d))
      
  lpc = len(pcombinations)
  print "There are %d valid combinations of %d tetrominoes within the %d possibilities." % (lpc, PIECES, lc) 
  if args.out_pc:
    pickle.dump(pcombinations, open(args.out_pc,'wb'))
    print "Output saved to '%s'." % args.out_pc
  
if __name__ == "__main__":
  parser = argparse.ArgumentParser(
    description='Computes a Tetris decision tree for a NxM sized grid'
  )

  parser.add_argument('--width', metavar='WIDTH', type=int,
    default=4, help='width of Tetris grid')
  parser.add_argument('--height', metavar='HEIGHT', type=int,
  default=4, help='height of Tetris grid')

  pin = parser.add_mutually_exclusive_group()
  pin.add_argument('--in-p', metavar='IN_P', type=str,
    help='import possibilities and resume program')
  pin.add_argument('--in-c', metavar='IN_C', type=str,
    help='import combinations and resume program')
  pin.add_argument('--in-pc', metavar='IN_PC', type=str,
    help='import possible combinations and resume program')

  pout = parser.add_argument_group('output')
  pout.add_argument('--out-p', metavar='OUT_P', type=str,
    default='possibilities.p', help='save possibilities [default: possibilities.p]')
  pout.add_argument('--out-c', metavar='OUT_C', type=str,
    default='combinations.p', help='save combinations [default: combinations.p]')
  pout.add_argument('--out-pc', metavar='OUT_PC', type=str,
    default='pcombinations.p', help='save possible combinations [default: pcombinations.p]')
    
  args = parser.parse_args()

  WIDTH  = args.width   # Width of board
  HEIGHT = args.height  # Height of board
  
  if args.in_pc:
    exit('in-pc currently unimplemented')
  elif args.in_c:
    c = pickle.load( open(args.in_c,'rb') )  
    calculate_pcombinations(c)
  elif args.in_p:
    p = pickle.load( open(args.in_p,'rb') )
    calculate_combinations(p)
  else:
    calculate_possibilities()
