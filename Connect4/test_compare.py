import game
import time
import calcweight
import calcsum

if __name__ == "__main__":
    testgame = game.Game(player = 0)
    # aiMove = calcMove(game, 5)
    # print(f'AI moves {aiMove}')
    # game.play(game.current_player, aiMove)
    print(testgame.draw())
    while testgame.winner < 0:
        while testgame.current_player == 0:
            aiMove = calcweight.calcMove(testgame, 0, 9)
            if aiMove > 0:
                print(f'AI-0 moves {aiMove}')
                testgame.play(testgame.current_player, aiMove, True)
                print(testgame.draw())
                time.sleep(1)
                if testgame.winner > -1:
                    break
            else:
                break
        while testgame.current_player == 1:
            aiMove = calcsum.calcMove(testgame, 6)
            if aiMove > 0:
                print(f'AI-1 moves {aiMove}')
                testgame.play(testgame.current_player, aiMove, True)
                print(testgame.draw())
                time.sleep(1)
                if testgame.winner > -1:
                    break
            else:
                break
    else:
        print("Game over! The winner is player " + str(testgame.winner) + "!")