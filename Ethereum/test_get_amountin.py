reserve0 = 51644237373818564
reserve1 = 3960599655807902020650
amount_in = 1000000000
amount_in *= 0.997

numerator = reserve1 * amount_in * 10000
denominator = (reserve0 + amount_in) * 10000
amount_out = numerator / denominator 
print(f"Amount Out: {amount_out }")