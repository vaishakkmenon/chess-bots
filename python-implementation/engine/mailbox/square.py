# Temporary Square class for later to represent each square on a board
# Used for GUI maybe


class Square:

    def __init__(self, file, rank):
        self._file = file
        self._rank = rank

    @property
    def file(self):
        return self._file

    @property
    def rank(self):
        return self._rank

    def __repr__(self):
        print("Square: f{file}{rank}")
