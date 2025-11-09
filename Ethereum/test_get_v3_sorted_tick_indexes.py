from decimal import Decimal, getcontext, ROUND_FLOOR

# 1) increase precision so logs & multiplies are rock-solid
getcontext().prec = 100

Q96       = 2**96
FEE_TIER  = 3000
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
sorted_tick_indexes = [-46080, -44640, -43800, -41820, -41340, -40860, -40560, -39120, -37320, -33300, -30900, -29940, -28920, -28320, -28020, -27720, -27600, -27480, -27360, -27060, -25680, -24840, -24000, -23040, -19440, -17940, -16080, -15480, -14700, -13860, -11820, -10980, -6960, -5640, -5280, -4080, -3480, -3300, -2280, -1800, -180, -120, 0, 60, 120, 180, 240, 540, 780, 1080, 1320, 1380, 1440, 2220, 2460, 2520, 2580, 2640, 3360, 3420, 3540, 4020, 4080, 4140, 4200, 4260, 4320, 4380, 4440, 4500, 4560, 4620, 4680, 4980, 5040, 5100, 5220, 5280, 5340, 5460, 5520, 5640, 5700, 6000, 6420, 6720, 6840, 6960, 7140, 7320, 7380, 7860, 7980, 8220, 8280, 8700, 9120, 9180, 9300, 9420, 9660, 9780, 9900, 9960, 10200, 10380, 10440, 10500, 10680, 10800, 10980, 11700, 11820, 12000, 12060, 12240, 12900, 13080, 13560, 13620, 13680, 13740, 13860, 13920, 13980, 14040, 14100, 14160, 14220, 14280, 14340, 14400, 14460, 14520, 14580, 14640, 14700, 14880, 15120, 15480, 15540, 15600, 15660, 15720, 15780, 15840, 15900, 15960, 16020, 16080, 16260, 16320, 16380, 16440, 16500, 16620, 16740, 16800, 16860, 16920, 16980, 17040, 17100, 17160, 17220, 17280, 17340, 17400, 18240, 18300, 18960, 19080, 19140, 19680, 20400, 20580, 21720, 22440, 22620, 22680, 23040, 23220, 23280, 23340, 23460, 23520, 23640, 23700, 23820, 24000, 24060, 24120, 24180, 24240, 24300, 24360, 24720, 24780, 24840, 24900, 24960, 25020, 25080, 25140, 25200, 25260, 25320, 25380, 25440, 25500, 25560, 25620, 25680, 25740, 25800, 25860, 25920, 25980, 26040, 26100, 26160, 26220, 26280, 26340, 26400, 26460, 26520, 26580, 26640, 26700, 26760, 26820, 26880, 26940, 27000, 27060, 27120, 27180, 27240, 27300, 27360, 27420, 27480, 27540, 27600, 27660, 27720, 27780, 27840, 27900, 27960, 28020, 28080, 28140, 28200, 28260, 28320, 28380, 28440, 28500, 28560, 28620, 28680, 28740, 28800, 28860, 28920, 28980, 29040, 29100, 29160, 29220, 29280, 29340, 29400, 29460, 29520, 29580, 29640, 29700, 29760, 29940, 30180, 30420, 30540, 30600, 30720, 30840, 31020, 31140, 31260, 31320, 31380, 31440, 31620, 31680, 31740, 31800, 31920, 31980, 32040, 32100, 32160, 32220, 32340, 32400, 32460, 32520, 32580, 32640, 32700, 32760, 32820, 32880, 33000, 33180, 33300, 33420, 33540, 33720, 34140, 34320, 34500, 34560, 34620, 34740, 34800, 34860, 34980, 35040, 35100, 35280, 35340, 35400, 35460, 35640, 35880, 35940, 36000, 36240, 36300, 36420, 36480, 36600, 36660, 36720, 36900, 37020, 37080, 37140, 37260, 37320, 37380, 37500, 37560, 37980, 38220, 38280, 38400, 38460, 38520, 38580, 38640, 38700, 38760, 38820, 38880, 38940, 39000, 39060, 39120, 39180, 39240, 39300, 39360, 39420, 39480, 39540, 39600, 39660, 39720, 39780, 39840, 39900, 39960, 40020, 40080, 40140, 40200, 40260, 40320, 40380, 40440, 40500, 40560, 40620, 40680, 40740, 40800, 40860, 40920, 40980, 41040, 41100, 41160, 41220, 41280, 41340, 41400, 41460, 41520, 41580, 41640, 41700, 41760, 41820, 41880, 41940, 42000, 42060, 42120, 42180, 42240, 42300, 42360, 42420, 42480, 42540, 42600, 42660, 42720, 42780, 42840, 42900, 42960, 43020, 43080, 43140, 43200, 43260, 43320, 43620, 43740, 43800, 44400, 44640, 44700, 44940, 45000, 45300, 45540, 45780, 45960, 46080, 46260, 46320, 46380, 46740, 46800, 46920, 46980, 47040, 47100, 47820, 48060, 48600, 49020, 49740, 50100, 51840, 52920, 52980, 55140, 56520, 57060, 57120, 58080, 58740, 61680, 62160, 63180, 63300, 63660, 63720, 65700, 67620, 69060, 69120, 69600, 70920, 73380, 81120, 81780, 85200, 91980, 92100, 98640, 108180, 114060, 114180, 115140, 121320]
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    res = exact_output_swap(
        sorted_tick_indexes,
        current_tick=32484,
        sqrt_price_x96=402017553926558663022017784141,
        liquidity=199050111124258962914,
        exact_output=6445039999999999000000
    )
    print(f"amount0     : {res['amount0']}")
    print(f"amount1     : {res['amount1']}")
    print(f"sqrtPriceX96: {res['sqrtPriceX96']}")
    print(f"liquidity   : {res['liquidity']}")
    print(f"tick        : {res['tick']}")
