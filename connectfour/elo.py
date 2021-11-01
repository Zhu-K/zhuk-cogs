import math
  
def prob(rating0, rating1):
    return 1.0 / (1.0 + math.pow(10, float(rating0 - rating1) / 400))
  
def calcElo(R0, R1, K, d):

    P1 = prob(R0, R1)
    P0 = 1.0 - P1
  
    R0 += K * ((1 - d) - P0)
    R1 += K * (d - P1)

    return (int(R0), int(R1))