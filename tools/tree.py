from piece_definitions import PIECES
import numpy as np
import collections

# Error raised when offset function cannot fit piece in
class PieceNotFitError(ValueError):
  pass
  
# Board represents a board with a given width and height  
class Board(object):
  def __init__(self, height, width):
    self._width = width
    self._height = height
  
  #
  #   |
  # ^ |
  # h |
  #   |
  #   |____________
  #  0     w >
  #
  # The offset function attempts to place a smaller 2D-array "a" in a height*width
  # sized 2D-array with offsets of "h" and "w" as per the diagram above.
  def offset(self, a, h, w):
    a_height = a.shape[0]
    a_width = a.shape[1]

    if (a_height + h) > self._height or (a_width + w) > self._width:
      raise PieceNotFitError, "Shape with given offset cannot fit within dimensions"
    
    rows = []
    
    start_height = self._height - (h + a_height)
    end_height = start_height + a_height
    
    for i in range(self._height):
      if i >= start_height and i < end_height:
        rows.append([False]*w + list(a[i - start_height]) + [False]*(self._width - w - a_width))
      else:
        rows.append([False]*self._width)
        
    return np.array(rows)
    
  # The get_piece function returns an piece with the appropriate rotation
  def get_piece(self, type, rotation):
    return np.rot90(PIECES[type], rotation)
    
  # To byte matrix merges multiple DActions into one numpy byte array with
  # a different byte representing each piece.
  # Behavior is undefined when the DActions overlap, so don't do that.
  def to_byte_matrix(self, dactions):
    board = np.zeros((self._height, self._width), np.uint8)
    for j, da in enumerate(dactions, 1):
      new = da.data.astype(np.uint8, copy=True)
      num = j
      nz = np.nonzero(da.data)
      for i in range(len(nz[0])):
        new[nz[0][i], nz[1][i]] = num
      board = np.bitwise_or(board, new)
    return board
  
  # Represents the utility of a current matrix boolean
  # Modification of Nathan's utility function in utility.py
  def utility(self, board):
    if np.all(board): # A filled board has infinite utility
      return float('inf')
  
    UTILITY_ADJACENT_TO_BLOCK = 1
    UTILITY_ADJACENT_TO_WALL = 10
    UTILITY_ADJACENT_TO_FLOOR = 1
    UTILITY_HOLE = -80

    utility = 0

    for row in range(0, self._height):
      for column in range(0, self._width):
        if board[row, column]:
          positions = ((row - 1, column),
                       (row + 1, column),
                       (row, column - 1),
                       (row, column + 1))
          for pos in positions:
            try:
              if pos[1] == -1 or pos[1] == self._width:
                  utility += UTILITY_ADJACENT_TO_WALL
              elif pos[0] == -1:
                  utility += UTILITY_ADJACENT_TO_FLOOR
              elif board[pos[0], pos[1]]:
                  utility += UTILITY_ADJACENT_TO_BLOCK
            except IndexError:
              pass
        else:
          # check for holes
          for i in range(row + 1, self._height):
            if board[i, column]:
              utility += UTILITY_HOLE
              break;

    return utility
      
  # Returns a unique hash for each matrix' dimensions
  # Hash is only unique for matricies of the same dimension
  def matrix_hash(self, x):
    return long(''.join(['1' if e else '0' for e in np.reshape(x, -1)]), 2)

# Action represents an action
class Action(object):
  def __init__(self, board, piece, rotation, h, w):
    if not (isinstance(piece, int) and isinstance(rotation, int)
      and isinstance(h, int) and isinstance(w, int)):
      raise ValueError, "Incorrect parameters"
  
    self.board = board
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
# matrix representing the piece's position on a heightxwidth plain.
# "data" attribute is very useful in performing calculations on pieces.
class DAction(Action):
  def __init__(self, board, piece, rotation, h, w):
    super(DAction, self).__init__(board, piece, rotation, h, w)
    self.data = board.offset(board.get_piece(piece, rotation), h, w)

  # Returns piece without representative matrix
  def get_action(self):
    return Action(self.board, self.piece, self.rotation, self.h, self.w)
    
  def __repr__(self):
    return "DA(p:%s r:%s h:%s w:%s)" % (self.piece, self.rotation, self.h, self.w)
  
# State represents a current state of the game
# Board is a height * width NumPy boolean array
class State(object):
  def __init__(self, board, parent, board_state):
    # Actions are indexes to new states, indexed by piece type for performance
    # e.g.
    # piece_type = 0
    # action = Action(p:0 r:1 h:0 w:0)
    # self.actions[piece_type][action]
    self.actions = collections.defaultdict(dict)
    self.board = board
    self.parent = parent # Parent state
    self.utility = board.utility(board_state) # Utility of this state
    self.max_utility = float('-inf') # Maximum utility of the actions under this state
    self._bhash = board.matrix_hash(board_state) # Stores unique representation of state

  def __repr__(self):
    return "S(%s, u:%.2f, mu:%.2f)" % (hex(self.__hash__())[2:-1], self.utility, self.max_utility)

  def __hash__(self):
    s = "%d%d" %(id(self.parent), self._bhash)
    return int(s)