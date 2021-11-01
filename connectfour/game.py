from .board import Board
import random

pieces = {
    -1: ":new_moon:",
    0: ":yellow_circle:",
    1: ":red_circle:"
}

nums = {
    1: "1️⃣",
    2: "2️⃣",
    3: "3️⃣",
    4: "4️⃣",
    5: "5️⃣",
    6: "6️⃣",
    7: "7️⃣"
}

reactions = {
    "1️⃣" : 1,
    "2️⃣" : 2,
    "3️⃣" : 3,
    "4️⃣" : 4,
    "5️⃣" : 5,
    "6️⃣" : 6,
    "7️⃣" : 7
}

class Game(Board):
    def __init__(self, code, maxtime = 30, player = 0) -> None:
        super().__init__()
        self.reset()
        self.current_player = player
        self.players = []
        self.status = 0
        self.code = code
        self.message = None
        self.elos = []
        self.max_time = maxtime
        self.time = self.max_time

    # def __hash__(self) -> int:
    #     return hash(self.code)

    def join(self, player, rating):
        if len(self.players) < 2:
            self.players.append(player)
            self.elos.append(rating)
            if len(self.players) == 2:
                self.current_player = random.getrandbits(1)           # randomize starting player
                self.status = 1
                    
    def draw(self):
        drawing = ''
        for row in range(self.height - 1, 0, -1):
            for col in range(self.width):
                drawing += pieces[self.cells[col][row]]
            drawing += '\n'

        for col in range(self.width):
            drawing += nums[col + 1]

        return drawing

    def getStatus(self):
        if self.status == 4:
            return 'Game forfeited'
        elif self.status == 5:
            return 'Timed out'

        if self.winner > -1:
            if self.winner == 2:
                self.status = 3
            else:
                self.status = 2

        if self.status == 0:
            return 'Waiting for Opponent'
        elif self.status == 1:
            return 'In Progress'
        elif self.status == 2:
            return 'Game Over'
        elif self.status == 3:
            return 'Tied Game'
