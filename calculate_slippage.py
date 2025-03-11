def cal_slippage(reserve0, reserve1, dx, dy, f=0.003):
    k = reserve1 * reserve0
    if dx > 0: 
        return reserve1 - k / (reserve0 + dx * (1 - f))
    elif dy > 0:
        return reserve0 - k / (reserve1 + dy * (1 - f))
    return 0


reserve0 = 5163571854425867992801681
reserve1 = 2405844604325271181637

print(cal_slippage(reserve0, reserve1, 0, 3261217484088194341))