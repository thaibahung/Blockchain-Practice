def cal_slippage(t0, t1, a, b, f=0.003):
    k = t1 * t0
    initial_price = 1

    if a > 0: 
        return t1 - k / (t0 + a * (1 - f))
    elif b > 0:
        return t0 - k / (t1 + b * (1 - f))
    
    return 0


t0 = 5163571854425867992801681
t1 = 2405844604325271181637

print(cal_slippage(t0, t1, 0, 3261217484088194341))
# print(6969009102853315217399 / (6.95019483883927e+21) * 100