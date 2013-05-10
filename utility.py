import board
import move

def utility_function_a(board):
    UTILITY_OF_ROW = -100
    UTILITY_ADJACENT_TO_BLOCK = 1
    UTILITY_ADJACENT_TO_WALL = 10
    UTILITY_ADJACENT_TO_FLOOR = 1
    UTILITY_HOLE = -80

    utility = 0

    for row in range(0, board.get_num_rows()):
        utility += UTILITY_OF_ROW
        for column in range(0, board.get_width()):
            if board.block_at(row, column):
                positions = ((row - 1, column),
                             (row + 1, column),
                             (row, column - 1),
                             (row, column + 1))
                for pos in positions:
                    if board.is_wall(pos[1]):
                        utility += UTILITY_ADJACENT_TO_WALL
                    elif board.is_floor(pos[0]):
                        utility += UTILITY_ADJACENT_TO_FLOOR
                    elif board.block_at(pos[0], pos[1]):
                        utility += UTILITY_ADJACENT_TO_BLOCK
            else:
                # check for holes
                for i in range(row + 1, board.get_num_rows()):
                    if board.block_at(i, column):
                        utility += UTILITY_HOLE
                        break;
                    # end if
                # end for i
            # end if
        # end for column
    # end for row

    return utility

def test():
    b = board.Board(11)
    
    b.apply_move(move.Move(1, 1, 0))
    b.apply_move(move.Move(1, 1, 4))
    b.apply_move(move.Move(1, 1, 2))
    b.print_grid()
    print(utility_function_a(b))
