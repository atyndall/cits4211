import collections

UNICODE = True # Unicode support is present in system

# The print_multi_board function prints out a representation of the [0..inf]
# 2D-array as a set of HEIGHT*WIDTH capital letters (or # if nothing is there).      
def print_multi_board(a):
  for row in a:
    print(''.join(['#' if e == 0 else chr(64 + e) for e in row]))
    
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