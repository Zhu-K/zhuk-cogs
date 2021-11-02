import game
#import calcweight
import time

if __name__ == "__main__":
    testgame = game.Game(player = 1)
    print(testgame.draw())
    while testgame.winner < 0:
        while testgame.current_player == 0:
            move = ''
            while not move.isnumeric():
                move = input("Player 0 move: ")
            if move == '0':
                break
            testgame.play(testgame.current_player, int(move) - 1)
            print(testgame.draw())
            print(testgame.cells)
            if testgame.winner > -1:
                break
        while testgame.current_player == 1:
            move = ''
            while not move.isnumeric():
                move = input("Player 1 move: ")
            if move == '0':
                break
            testgame.play(testgame.current_player, int(move) - 1)
            print(testgame.draw())
            print(testgame.cells)
            if testgame.winner > -1:
                break
    else:
        print("Game over! The winner is player " + str(testgame.winner) + "!")