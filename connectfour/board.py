# column 0 is the count of pieces in current row
class Board:
    def __init__(self, cells = [[0] * 7 for _ in range(7)], player = 0) -> None:
        self.cells = cells
        self.current_player = player
        self.winner = -1
        self.width = len(self.cells)
        self.height = len(self.cells[0])
        self.free_cells = (self.height - 1) * self.width - sum([col[0] for col in cells])

    def reset(self):
        for i in range(len(self.cells)):
            for j in range(len(self.cells[0])):
                if j == 0:
                    self.cells[i][j] = 0
                else:
                    self.cells[i][j] = -1
                self.winner = -1

    def play(self, player, index, verbose = False):
        if player == self.current_player:
            if self.width > index >= 0:
                if verbose:
                    pass
                    #print(f"playing index {index}")
                if self.cells[index][0] < self.height - 1:
                    if self._playRaw(player, index, self.cells[index][0] + 1):
                        return 1
                        # game ended
                    else:
                        self.current_player = 1 - self.current_player
                else:
                    pass
                    # column full, can't add
            else:
                pass
                # invalid index, out of bounds
        else:
            pass
            # not your turn!

    def _playRaw(self, player, col, row):
        # returns True if game ends after this play
        
        self.cells[col][0] = row                # increment column piece count
        self.cells[col][row] = player           # place piece
        self.free_cells -= 1
        print(f"free cells: {self.free_cells}")
        # check vertical for win
        i = 1
        while i < 4:
            if row - i < 1 or self.cells[col][row - i] != player:
                break
            i += 1
        for j in range(1, 5 - i):
            if row + j >= self.height or self.cells[col][row + j] != player:
                break
        else:
            self.winner = player
            return True

        # check horizontal for win
        i = 1
        while i < 4:
            if col - i < 0 or self.cells[col - i][row] != player:
                break
            i += 1
        for j in range(1, 5 - i):
            if col + j >= self.width or self.cells[col + j][row] != player:
                break
        else:
            self.winner = player
            return True

        # check left-diagonal for win
        i = 1
        while i < 4:
            if col - i < 0 or row - i < 1 or self.cells[col - i][row - i] != player:
                break
            i += 1
        for j in range(1, 5 - i):
            if col + j >= self.width or row + j >= self.height or self.cells[col + j][row + j] != player:
                break
        else:
            self.winner = player
            return True

        # check right-diagonal for win
        i = 1
        while i < 4:
            if col - i < 0 or row + i >= self.height or self.cells[col - i][row + i] != player:
                break
            i += 1
        for j in range(1, 5 - i):
            if col + j >= self.width or row - j < 1 or self.cells[col + j][row - j] != player:
                break
        else:
            self.winner = player
            return True
        
        if self.free_cells == 0:
            self.winner = 2     # tie
            return True