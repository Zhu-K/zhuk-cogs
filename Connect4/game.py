import board

# sym = {
#     'TL' : '╔',
#     'TR' : '╗',
#     'BL' : '╚',
#     'BR' : '╝',
#     'H'  : '═',
#     'V'  : '║',
#     'LT' : '╠',
#     'RT' : '╣',
#     'TT' : '╦',
#     'BT' : '╩',
#     'X'  : '╬',
# }

sym = {
    -1: ". ",
    0: "X ",
    1: "O "
}

class Game(board.Board):
    def __init__(self, player = 0) -> None:
        super().__init__()
        self.reset()
        self.current_player = player

    def draw(self):
        drawing = ''
        for row in range(self.height - 1, 0, -1):
            for col in range(self.width):
                drawing += sym[self.cells[col][row]]
            drawing += '\n'

        for col in range(self.width):
            drawing += str(col + 1) + ' '

        return drawing