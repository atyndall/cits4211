from piece_definitions import pieces
import numpy as np
import sys
import collections
import itertools
from math import factorial
import cPickle as pickle

WIDTH  = 4 # Width of board
HEIGHT = 4 # Height of board
PIECES = (WIDTH * HEIGHT) / 4 # Number of pieces that can fit in board

# Define a data structure to hold the piece information
NonHashPiece = collections.namedtuple('Piece', ['type', 'rotation', 'h', 'w', 'data'])
class OrientedPiece(NonHashPiece):
  def __hash__(self):
    h = "%d%d%d%d" % (self.type, self.rotation, self.h, self.w)
    return int(h)

# The print_board function prints out a representation of the [True, False]
# 2D-array as a set of HEIGHT*WIDTH empty and filled Unicode squares.
def print_board(a):
  for row in a.data:
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
       
# Calculate every possible position a piece can have on a WIDTH*HEIGHT grid
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
        
# We permute over all possible combinations and rotations of pieces to see which
# successfully fit together.
lp = len(possibilities)
search_space = factorial(lp) / ( factorial(lp-PIECES) * factorial(PIECES) )
combinations = []
i = 0
for i, en in enumerate( itertools.combinations(possibilities, PIECES) ):
  a, b, c, d = en
  first = np.logical_and(a.data, b.data)
  
  if not np.any(first):
    ab = np.logical_or(a.data, b.data)
    second = np.logical_and(ab, c.data)
    
    if not np.any(second):
      abc = np.logical_or(ab, c.data)
      third = np.logical_and(abc, d.data)
      
      if not np.any(third):
        combinations.append((a,b,c,d))     

  if i % (search_space/250) == 0: # Output a message every now and then with progress
    print "Searched %d/%d combinations (%.1f%% complete)" % (i, search_space, (i/float(search_space))*100)
    

pickle.dump(combinations, open('combinations.p', 'wb'))