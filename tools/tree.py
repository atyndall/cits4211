from piece_definitions import PIECES
import numpy as np
import collections

# TODO: TEMP FIX, PLEASE UNDO
WIDTH = 4   # Default width
HEIGHT = 4  # Default height

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
# Board is a HEIGHT * WIDTH NumPy boolean array
class State(object):
  def __init__(self, parent, board):
    # Actions are indexes to new states, indexed by piece type for performance
    # e.g.
    # piece_type = 0
    # action = Action(p:0 r:1 h:0 w:0)
    # self.actions[piece_type][action]
    self.actions = collections.defaultdict(dict)
    
    self.parent = parent # Parent state
    self.utility = utility(board) # Utility of this state
    self.max_utility = float('-inf') # Maximum utility of the actions under this state
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