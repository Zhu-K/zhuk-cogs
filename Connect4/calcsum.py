import board

def recurse(gameboard, player, depth, maxdepth):
    if depth == maxdepth:
        return [gameboard.getScore(0), gameboard.getScore(1)]
    else:
        sums = [0, 0]
        for i in range(1, 7):
            if gameboard.cells[i + player * 7] > 0:
                nextBoard = board.Board(gameboard.cells.copy(), player)
                nextBoard.play(player, i)
                result = recurse(nextBoard, nextBoard.current_player, depth + 1, maxdepth)
                sums[0] += result[0]
                sums[1] += result[1]
        return sums

def calcMove(gameboard, maxdepth):
    results = [-99999] * 7
    currentmax = 0
    for i in range(1, 7):
        if gameboard.cells[i + gameboard.current_player * 7] > 0:
            nextBoard = board.Board(gameboard.cells.copy(), gameboard.current_player)
            nextBoard.play(gameboard.current_player, i)
            result = recurse(nextBoard, gameboard.current_player, 0, maxdepth)
            results[i] = result[1] - result[0]
            if results[i] > results[currentmax]:
                currentmax = i
                #print(result)
    return currentmax