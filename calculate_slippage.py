def cal_slippage(t0, t1, a, b, f=0.00253):
    k = t1 * t0
    initial_price = 1
    
    if a > 0:
        return t1 - k /(t0 + a * (1 - f)), 0, 0
    else:
        return 0, 0, 0

    if a > 0: 
        initial_price = t1 / t0
        new_price = k / (t0 + a * (1 - f)) ** 2
        return t0 + a * (1 - f), k / (t0 + a * (1 - f)), -(new_price - initial_price) / initial_price
    
    if b > 0:
        initial_price = t0 / t1
        new_price = k / (b * (1 - f) + t1) ** 2
        return k / (t1 + b * (1 - f)), t1 + b * (1 - f), -(new_price - initial_price) / initial_price
    
    return 0


t0 = 5147933775953925071084224
t1 = 2413105297758992121711
f = 0.003

print(cal_slippage(t0, t1, 1228467654158204134467, 0)[0])

trade = [(10, 0), (0, 10), (34, 0), (33, 0), (0, 101), (0, 73)]
my_tx = (0, 31)

slippage_1 = 0
slippage_2 = 0
total_a = 0
total_b = 0

for a, b in trade:
    total_a += a
    total_b += b
    t0, t1, _ = cal_slippage(t0, t1, a, b)
    # print(t0, t1, t0 * t1)

slippage_1 = cal_slippage(t0, t1, my_tx[0], my_tx[1])[2]

t1 = 1000
t0 = 3000
t1, t0, _ = cal_slippage(t0, t1, total_a, 0)
t1, t0, _ = cal_slippage(t0, t1, 0, total_b)
slippage_2 = cal_slippage(t0, t1, my_tx[0], my_tx[1])[2]

# print(slippage_1)