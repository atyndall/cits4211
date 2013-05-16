# Requires Python 2.7

import sys
# Add the parent directory to the python path so that we can import files there
sys.path.append("..")

from tree import *

import pickle

import numpy as np # get at http://www.scipy.org/Download

# Unpickle a pregenerated tree
tree = pickle.load( open('tree.p','rb') )

print "Successfully imported 'tree', try playing around with it!"
print "Type 'exit()' to quit."

# Enter into an interactive shell
import code
vars = globals().copy()
vars.update(locals())
shell = code.InteractiveConsole(vars)
shell.interact()