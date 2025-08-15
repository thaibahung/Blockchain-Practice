from decimal import Decimal, getcontext, ROUND_FLOOR

# 1) increase precision so logs & multiplies are rock-solid
getcontext().prec = 100

Q96       = 2**96
FEE_TIER  = 2500
FEE_DENOM = 10**6

def tick_to_sqrt_price_x96(tick: int) -> int:
    # √(1.0001^tick) * 2**96
    return int(
        (Decimal('1.0001') ** (Decimal(tick) / 2)) 
        * Decimal(Q96)
        .to_integral_value(rounding=ROUND_FLOOR)
    )

def get_amount0_delta(L: int, sa: int, sb: int, round_up: bool) -> int:
    num = L * (sb - sa) * Q96
    den = sb * sa
    return (num + den - 1)//den if round_up else num//den

def get_amount1_delta(L: int, sa: int, sb: int, round_up: bool) -> int:
    diff = sb - sa
    num  = L * diff
    return (num + Q96 - 1)//Q96 if round_up else num//Q96

def apply_fee(amount_wo_fee: int) -> int:
    num = amount_wo_fee * FEE_DENOM
    den = FEE_DENOM - FEE_TIER
    return (num + den - 1)//den

def get_tick_at_sqrt_price(sqrtPriceX96: int) -> int:
    # initial guess via logs
    ratio     = Decimal(sqrtPriceX96) / Decimal(Q96)
    raw_tick  = (ratio.ln() / Decimal('1.0001').ln()) * 2
    guess     = int(raw_tick)               # truncates toward zero
    # now “walk” up or down until tick_to_sqrt_price_x96(guess) ≤ sqrtPrice < next
    sp_guess  = tick_to_sqrt_price_x96(guess)
    if sp_guess > sqrtPriceX96:
        while tick_to_sqrt_price_x96(guess) > sqrtPriceX96:
            guess -= 1
    else:
        while tick_to_sqrt_price_x96(guess + 1) <= sqrtPriceX96:
            guess += 1
    return guess

def exact_output_swap(
    sorted_ticks: list[int],
    current_tick: int,
    sqrt_price_x96: int,
    liquidity: int,
    exact_output: int
):
    out_rem  = exact_output
    in_tot   = 0
    cur_sp   = sqrt_price_x96

    # find first tick above current
    idx = 0
    while idx < len(sorted_ticks) and sorted_ticks[idx] <= current_tick:
        idx += 1

    # march ticks upward
    while out_rem > 0 and idx < len(sorted_ticks):
        next_tick     = sorted_ticks[idx]
        boundary_sp   = tick_to_sqrt_price_x96(next_tick)
        max_out_here  = get_amount0_delta(liquidity, cur_sp, boundary_sp, False)
        print(next_tick, boundary_sp, max_out_here)

        if max_out_here >= out_rem:
            # **partial**: solve new_sp exactly
            num   = liquidity * Q96 * cur_sp
            den   = liquidity * Q96 - out_rem * cur_sp
            new_sp = (num + den - 1) // den   # ceil division

            # input needed
            amt1   = get_amount1_delta(liquidity, cur_sp, new_sp, True)
            in_tot +=   amt1

            cur_sp       = new_sp
            current_tick = get_tick_at_sqrt_price(cur_sp)
            out_rem      = 0
            break

        # full tick cross
        amt1   = get_amount1_delta(liquidity, cur_sp, boundary_sp, True)
        in_tot += amt1
        out_rem -= max_out_here

        cur_sp       = boundary_sp
        current_tick = next_tick
        idx         += 1

    return {
        "amount0":      -exact_output,
        "amount1":       apply_fee(in_tot),
        "sqrtPriceX96":  cur_sp,
        "liquidity":     liquidity,
        "tick":          current_tick
    }

# ─── your full tick list here ───────────────────────────────
sorted_tick_indexes = [-138150, -111100, -107300, -106000, -105700, -103900, -103150, -101700, -101550, -99750]
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    res = exact_output_swap(
        sorted_tick_indexes,
        current_tick=-104132,
        sqrt_price_x96=434309731157713468822207725,
        liquidity=45102370403373399956099,
        exact_output=6445039999999999000000
    )
    print(f"amount0     : {res['amount0']}")
    print(f"amount1     : {res['amount1']}")
    print(f"sqrtPriceX96: {res['sqrtPriceX96']}")
    print(f"liquidity   : {res['liquidity']}")
    print(f"tick        : {res['tick']}")
