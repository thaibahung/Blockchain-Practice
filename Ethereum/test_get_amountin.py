reserve0 = 3960599655807902020650
reserve1 = 51644237373818564
amount_in = 1000000000
amount_in *= 0.997

numerator = reserve1 * amount_in * 10000
denominator = (reserve0 + amount_in) * 10000
amount_out = numerator / denominator 
print(f"Amount Out: {amount_out }")