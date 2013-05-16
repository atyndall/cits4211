from piece_definitions import pieces
import numpy as np
import sys
import collections
import itertools
import argparse
import multiprocessing
import time
from math import factorial
from rect import Rect
import cPickle as pickle

WIDTH = 4   # Default width
HEIGHT = 4  # Default height
PIECES = (WIDTH * HEIGHT) / 4 # Number of pieces that can fit in board
NUM_PIECES = len(pieces)
NOTIFY_INTERVAL = 10 # Number of seconds between progress notification
UNICODE = True # Unicode support is present in system

args = None

# Define a data structure to hold the piece information
class Piece(object):
  def __init__(self, ptype, rotation, h, w):
    if ptype is None or rotation is None or h is None or w is None:
      raise ValueError, "Required values not supplied"
      
    self.ptype = ptype
    self.rotation = rotation
    self.h = h
    self.w = w
    
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
    
  def __repr__(self):
    return "Piece(ptype=%s, rotation=%s, h=%s, w=%s)" % (self.ptype, self.rotation, self.h, self.w)

# Same as Piece data structure, except that it has a "data" attribute that contains a
# matrix representing the piece's position on a HEIGHTxWIDTH plain.
# "data" attribute is very useful in performing calculations on pieces.
class DataPiece(Piece):
  def __init__(self, ptype, rotation, h, w):
    super(DataPiece, self).__init__(ptype, rotation, h, w)
    self.data = offset(get_piece(ptype, rotation), h, w)

  # Returns piece without representative matrix
  def get_dataless(self):
    return Piece(self.ptype, self.rotation, self.h, self.w)
    
  def __repr__(self):
    return "DataPiece(ptype=%s, rotation=%s, h=%s, w=%s)" % (self.ptype, self.rotation, self.h, self.w)

# Tree represents the root node of a decision tree comprised of DNodes that index PNodes
class Tree(object):
  def __init__(self):
    self.children = [None] * NUM_PIECES # Children are PNodes, there is a fixed amount
    self.parent = None # Tree doesn't have a parent 
  
  def __repr__(self):
    return "Tree(%s)" % hex(id(self))
    
# DNodes represent decisions that contain a specific rotation and placement of a piece  
class DNode(object):
  def __init__(self, rotation, h, w):
    self.rotation = rotation
    self.h = h
    self.w = w
    
  def __repr__(self):
    return "DNode(%s)" % hex(id(self))
    
  def __str__(self):
    return "DNode(rotation=%s, h=%s, w=%s)" % (self.rotation, self.h, self.w)
    
  def __hash__(self):
    h = "%d%d%d" % (self.rotation, self.h, self.w)
    return int(h)
  
# PNodes represent pieces on the tree
class PNode(object):
  def __init__(self, parent, ptype):
    self.parent = parent # Parent node is another PNode
    self.children = {} # DNodes are indexes into new PNodes
    self.ptype = ptype

  def __repr__(self):
    return "PNode(%s)" % hex(id(self))
    
  def __str__(self):
    return "PNode(parent=%s, ptype=%s, n_child=%s)" % (self.parent, self.ptype, len(self.children))

  def __hash__(self):
    h = "%d%d" % (id(self.parent), self.ptype)
    return int(h)

# A decision node contains a pointer to a parent node (or None if root) and pointers to various
# children nodes
# MaxUtility = collections.namedtuple('MaxUtility', ['rotation', 'node', 'utility'])  
# class DNode(object):
  # max_utility = MaxUtility(None, None, float('-inf')) # Contains the maximum utility of all child nodes
  # utility = float('-inf') # Contains the utility of the board in which actions to this node are executed
  # type = None # Contains number identifying node
  
  # def __init__(self, parent):
    # global pieces
    # self._nchildren = len(pieces) # Holds number of children nodes
    # self.children = [[None] * self._nchildren] * 4 # Array indexes the rotation of the piece, then the child pieces that follow from that rotation
    
    # if len(children) != self._nchildren:
      # raise ValueError, "Incorrect number of children"
      
# def temp_tree(): return defaultdict(temp_tree)
      
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
  for n, p in enumerate(pieces):
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
            op = DataPiece(n, r, h, w)
            possibilities.append(op)
          except PieceNotFitError:
            pass

  lp = len(possibilities)
  print "There are %d possible orientations and positions for the given tetrominoes." % lp

  calculate_possible(possibilities)
 
# Check possibility
def check_possibility(cur_pieces):
  global pieces
  board = np.zeros((HEIGHT, WIDTH), np.bool)

  indr = [] # List of coordinate pairs of all pieces
  lowestc = [HEIGHT, WIDTH] # Lowest coordinate of all pieces: (bottom, left)
  highestc = [0, 0] # Highest coordinate of all pieces: (top, right)
  
  # TODO: Verify that optimisations work
  boxcalc = False
  prev_p = None
  prev_bounding = None
  for p in cur_pieces:
    pheight = len(pieces[p.ptype])
    pwidth = len(pieces[p.ptype][0])
    coords = [[p.h, p.w], [pheight + p.h, pwidth + p.w]]
    max_bounding = Rect(lowestc, highestc)
    cur_bounding = Rect(*coords) # (bottom, left), (top, right)
    
    if prev_p is not None and prev_bounding is not None:
      board = np.logical_or(prev_p.data, board)
      indr.append(prev_bounding)
    
    prev_p = p
    prev_bounding = cur_bounding
    
    # Optimisation is not currently providing better performance
    # # Check to see if coordinates collide with bounding box of all current
    # # tetronimos
    # if boxcalc and not max_bounding.overlaps(cur_bounding):
      # continue # There is no collision with the large bounding box, piece will fit
      
    # # Check to see if coordinates collide with individual piece bounding
    # # boxes
    # if len(indr) > 0:
      # overlap = False
      # for i_bounding in indr:
        # if cur_bounding.overlaps(i_bounding):
          # overlap = True
          # break
          
      # if not overlap:
        # continue # There is no collision with individual bounding boxes, piece will fit
          
    # indr.append(cur_bounding)
    
    # # Keep track of lowest coordinate
    # if coords[0][0] < lowestc[0]:
      # lowestc[0] = coords[0][0]
    # if coords[0][1] < lowestc[1]:
      # lowestc[1] = coords[0][1]
    
    # # Keep track of highest coordiate
    # if coords[1][0] > highestc[0]:
      # highestc[0] = coords[1][0]
    # if coords[1][1] > highestc[1]:
      # highestc[1] = coords[1][1]
      
    # boxcalc = True
    
    # We couldn't work out if it collides or not cheaply, so now onto the hard stuff
    if not possible(p.data, board):
      return None # This seems to have improved performance by like 10000%, very suspicious, keep an eye on it

  return cur_pieces
 
# Input seconds, output H:MM:SS
def time_remaining(s):
  hours, remainder = divmod(s, 3600)
  minutes, seconds = divmod(remainder, 60)
  return '%.f:%02.f:%02.f' % (hours, minutes, seconds)
 
# We combine all existing combinations and rotations of pieces to see which
# successfully fit together.
def calculate_possible(positions): 
  lp = len(positions)
  search_space = factorial(lp) / ( factorial(lp-PIECES) * factorial(PIECES) )
  
  print "Calculating possible combinations of tetrominoes from all placements (%d combinations)." % search_space
  start_time = time.time()
  
  combinations = []
  timer = time.time()
  prev_i = 0
  pool = multiprocessing.Pool() # Use multiple processes to leaverage maximum processing power
  #for i, res in enumerate( itertools.imap(check_possibility, itertools.combinations(positions, PIECES)) ):
  for i, res in enumerate( pool.imap_unordered(check_possibility, itertools.combinations(positions, PIECES), max(5, search_space/500)) ):
    if res:
      combinations.append(res)
    elapsed = time.time() - timer
    if elapsed > NOTIFY_INTERVAL and i != 0: # If x seconds have elapsed
      pps = (i-prev_i)/elapsed
      print "Searched %d/%d placements (%.1f%% complete, %.0f pieces/sec, ~%s remaining)" % (i, search_space, (i/float(search_space))*100, pps, time_remaining((search_space-i)/pps))
      prev_i = i
      timer = time.time()
  pool.terminate()
    
  lc = len(combinations)   
  print "There are %d possible combinations of %d tetrominoes within the %d positions." % (lc, PIECES, search_space)
  print "The calculation took %.1f." % time_remaining(time.time() - start_time)
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
  prev_i = 0
  pool = multiprocessing.Pool() # Use multiple processes to leaverage maximum processing power
  for possibility in possibilities:
    # We permute every combination to work out the orders in which it would be valid
    for i, res in enumerate( pool.imap_unordered(check_validity, itertools.permutations(possibility, PIECES), max(5,search_space/20)) ):
      if res:
        combinations.append([p.get_dataless() for p in res]) # We ditch the matricies as they are now unnecessary
        #combinations.append(res)
        # c = combinations
        # for p in res:
          # c[p] = {}
          # c = c[p]
            
      elapsed = time.time() - timer
      if elapsed > NOTIFY_INTERVAL and i != 0: # If x seconds have elapsed
        pps = (i-prev_i)/elapsed
        print "Searched %d/%d placements (%.1f%% complete, %.0f pieces/sec, ~%s remaining)" % (i, search_space, (i/float(search_space))*100, pps, time_remaining((search_space-i)/pps))
        prev_i = i
        timer = time.time()
  pool.terminate()
    
  lc = len(combinations)   
  print "There are %d valid permutations of %d tetrominoes within the %d possibilities." % (lc, PIECES, search_space)
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
  root = Tree()
  #root.utility = float('inf') # Utility of this action
  #root.max_utility = float('inf') # Maximum utility of action below this node in the tree
  #root.type = -1 # Root node has -1 type
  
  # Note: Optimal moves have a +inf utility
  
  for nodes in permutations:
    #cur_rot = None
    #cur_type = None
    cur_parent = root
    prev_p = None
    first = True
    for p in nodes:
      if first:
        root.children[p.ptype] = PNode(root, p.ptype)
        cur_parent = root.children[p.ptype].children
        prev_p = p
        first = False
      else:
        dnode = DNode(prev_p.rotation, prev_p.h, prev_p.w)
        pnode = PNode(root, p.ptype)
        cur_parent[dnode] = pnode
        cur_parent = pnode.children
    
      # cur_pnode = cur_parent.children[p.ptype]
      
      # Create a PNode and place it on the tree
      # if cur_parent.children[p.ptype] is None:
        # cur_pnode = PNode(cur_parent, p.ptype)
        # cur_parent.children[p.ptype] = cur_pnode
      
      # Create a DNode and place it on the tree    
      # cur_dnode = DNode(cur_pnode, p.rotation, p.h, p.w)
      # cur_pnode.children.add(cur_dnode)
      
      # cur_parent = cur_dnode

      
    
      # if p.ptype != cur_type:
        # cur_type = p.ptype
        
      # if p.rotation != cur_rot:
        # cur_rot = p.rotation
       
      # child_node = cur_node.children[cur_rot][cur_type]
       
      # if child_node is None:
        # child_node = DNode(cur_node)
  
  # Enter an interactive shell
  #import readline # optional, will allow Up/Down/History in the console
  import code
  vars = globals().copy()
  vars.update(locals())
  shell = code.InteractiveConsole(vars)
  shell.interact()
    
def print_tree(root, depth):
  print "Depth: %d" % depth
  if depth == 0:
    print root
  for c in root.children:
    print c
    time.sleep(1)
    print_tree(c, depth+1)
  
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
  PIECES = (WIDTH * HEIGHT) / 4
  
  if args.in_p:
    p = pickle.load( open(args.in_p,'rb') )
    calculate_valid(p)
  elif args.in_v:
    p = pickle.load( open(args.in_v,'rb') )
    create_tree(p)
  else:
    calculate_positions()
