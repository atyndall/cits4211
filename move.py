import sys

class Move:
    def __init__(self, piece, rotation, column):
        # Parameter checking
        if piece > 7 or piece < 1:
            raise Exception("Invalid value for piece")
        if rotation > 3 or rotation < 0:
            raise Exception("Invalid value for rotation")
        if column < 0:
            raise Exception("Invalid value for column")
        self._piece = piece
        self._rotation = rotation
        self._column  = column
        self._representation = self.make_representation()

    def make_representation(self):
        representation = ()
        if self._piece == 1:
            # I block
            if self._rotation == 0 or self._rotation == 2:
                representation = ((True,), (True,), (True,), (True,))
            else:
                representation = ((True, True, True, True),)
        elif self._piece == 2:
            # O block
            representation = ((True, True), (True, True))
            pass
        elif self._piece == 3:
            # T block
            if self._rotation == 0:
                representation = ((True, False), (True, True), (True, False))
            elif self._rotation == 1:
                representation = ((True, True, True), (False, True, False))
            elif self._rotation == 2:
                representation = ((False, True), (True, True), (False, True))
            elif self._rotation == 3:
                representation = ((False, True, False), (True, True, True))
        elif self._piece == 4:
            # L block
            if self._rotation == 0:
                representation = ((True, False), (True, False), (True, True))
            elif self._rotation == 1:
                representation = ((True, True, True), (True, False, False))
            elif self._rotation == 2:
                representation = ((True, True), (False, True), (False, True))
            elif self._rotation == 3:
                representation = ((False, False, True), (True, True, True))
        elif self._piece == 5:
            # J block
            if self._rotation == 0:
                representation = ((False, True), (False, True), (True, True))
            elif self._rotation == 1:
                representation = ((True, False, False), (True, True, True))
            elif self._rotation == 2:
                representation = ((True, True), (True, False), (True, False))
            elif self._rotation == 3:
                representation = ((True, True, True), (False, False, True))
        elif self._piece == 6:
            # S block
            if self._rotation == 0 or self._rotation == 2:
                representation = ((False, True), (True, True), (True, False))
            elif self._rotation == 1 or self._rotation == 3:
                representation = ((True, True, False), (False, True, True))
        elif self._piece == 7:
            # Z block
            if self._rotation == 0 or self._rotation == 2:
                representation = ((True, False), (True, True), (False, True))
            elif self._rotation == 1 or self._rotation == 3:
                representation = ((False, True, True), (True, True, False))
        return representation

    def print_representation(self):
        for row in reversed(self._representation):
            sys.stdout.write("|")
            for column in row:
                if column:
                    sys.stdout.write("X")
                else:
                    sys.stdout.write(" ")
                sys.stdout.write("|")
            sys.stdout.write("\n")

    def get_width(self):
        return len(self._representation[0])

    def get_height(self):
        return len(self._representation)

    def block_at(self, row, column):
        return self._representation[row][column]

    def get_piece(self):
        return self._piece

    def get_rotation(self):
        return self._rotation

    def get_column(self):
        return self._column

    def set_column(self, value):
        self._column = value

def print_all_representations():
        for i in range(1, 8):
            for j in range(0, 4):
                Move(i, j, 0).print_representation()
                sys.stdout.write("\n")
            sys.stdout.write("--------------------------\n") 

def test():
    print_all_representations()
