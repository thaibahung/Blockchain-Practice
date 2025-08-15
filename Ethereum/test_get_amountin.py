reserve0 = 170626938576825609987
reserve1 = 13403755766772696477761701
amount_in = 4500000000000000000000
amount_in *= 0.997

numerator = reserve0 * amount_in * 10000
denominator = (reserve1 + amount_in) * 10000
amount_out = numerator / denominator 
print(f"Amount Out: {amount_out }")