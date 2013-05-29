CITS4211 Tetris AI
========

An artificial intelligence that uses pre-generated placement decision trees to play a game of Tetris.
Refer to the included PDF report for more information.

This solution is written in Python 2.7, and the successful import of pre-generated PDTs cannot be guaranteed on a Python versions < 2.7.4, >= 3.

Project link: http://undergraduate.csse.uwa.edu.au/units/CITS4211/Project/13/assignment.html

Authors:
 * Ash Tyndall
 * Nathan Aplin
 
 
## Mini FAQ

1. I get `ImportError: No module named copy_reg`.
 * These is an issue with Pickle files and platform compatibility. Please regenerate the three pickle files in "trees" using tree_generator.py on your own system. They are [WIDTHxHEIGHT] `tree2.p` (2x4), `tree3.p` (3x4) and `tree4.p` (4x4).
2. Nothing happens when I run `solve.py` with no `--method` / `--method 0`.
 * You need to pick either method 1 or method 2.