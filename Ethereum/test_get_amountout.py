reserve0 = 7831488331603772239135
reserve1 = 19648337323592
amount_out = 403000000

numerator = reserve0 * amount_out * 10000
denominator = (reserve1 - amount_out) * 10000
amount_in = numerator // denominator
amount_in = amount_in * 1000 // 997  # Adjust for Uniswap's fee
print(f"Amount In: {amount_in}")