from Connect4.board import Board
import board

def _nextMove(gameboard : Board, player, alpha, beta, depth):
    if gameboard.winner == -1:      # no winners yet

        if player == 1:
            maxscore = (-999, -1)
            for i in range(7):
                if gameboard.cells[i][0] < gameboard.height - 1:        # still room to put piece
                    nextBoard = board.Board(gameboard.cells.copy(), gameboard.current_player)
                    nextBoard.play(gameboard.current_player, i)
                    score = (-999, -1)


        else:
            result = (999, -1)

        for i in range(7):
            if gameboard.cells[i][0] < gameboard.height - 1:        # still room to put piece
                nextBoard = board.Board(gameboard.cells.copy(), gameboard.current_player)
                nextBoard.play(gameboard.current_player, i)
                
        results.sort(reverse = (player == 1))
        if len(results) >= 3:
            return 0.5 * results[0] + 0.3 * results[1] + 0.2 * results[2]
        elif len(results) == 2:
            return 0.7 * results[0] + 0.3 * results[1]
        elif len(results) == 1:
            return results[0]

    # end game conditions
    elif gameboard.winner == 0:
        score = (gameboard.height - 1) * gameboard.width - gameboard.free_cells + 1
    elif gameboard.winner == 1:
        score = - ((gameboard.height - 1) * gameboard.width - gameboard.free_cells + 1)
    else:               # tie
        return 0

def calcMove(gameboard, aiplayer):
    maxmove = 0
    maxscore = -99999
    for i in range(7):
        if gameboard.cells[i][0] < gameboard.height - 1:        # still room to put piece
            nextBoard = board.Board(gameboard.cells.copy(), gameboard.current_player)
            nextBoard.play(gameboard.current_player, i)

            


        if aiplayer == 0:
            score *= -1
        if score > maxscore:
            maxscore = score
            maxmove = move
    return maxmove

    start = time.time()
    results = [-99999] * 7
    currentmax = 0
    for i in range(1, 7):

        if gameboard.cells[i + gameboard.current_player * 7] > 0:
            nextBoard = board.Board(gameboard.cells.copy(), gameboard.current_player)
            nextBoard.play(gameboard.current_player, i)
            results[i] = _nextMove(nextBoard, gameboard.current_player, 0, maxdepth)
            if aiplayer == 0:
                results[i] *= -1
            if results[i] > results[currentmax]:
                currentmax = i
                #print(result)
    print(f"Nonethreaded: elapsed time = {time.time() - start} seconds")
    return currentmax