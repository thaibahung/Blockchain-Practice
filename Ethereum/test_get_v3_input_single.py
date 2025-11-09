from math import log
from decimal import Decimal, getcontext

# ---- constants ----
Q96 = 2 ** 96
FEE_DENOM = 1_000_000  # 1e6 for Uniswap fee tiers (e.g., 500, 3000, 10000)

# increase precision only for logs (tick math)
getcontext().prec = 100


# ---------------------- Tick / Price Math ----------------------
def get_sqrt_ratio_at_tick(tick: int) -> int:
    """
    Equivalent to Uniswap's TickMath.getSqrtRatioAtTick()
    Computes sqrt(1.0001^tick) * 2^96 as integer (Q96)
    """
    ratio = Decimal("1.0001") ** (Decimal(tick) / 2)
    return int((ratio * Decimal(Q96)).to_integral_value(rounding="ROUND_FLOOR"))


def get_tick_at_sqrt_ratio(sqrt_price_x96: int) -> int:
    """
    Equivalent to Uniswap's TickMath.getTickAtSqrtRatio()
    """
    ratio = Decimal(sqrt_price_x96) / Decimal(Q96)
    raw_tick = (ratio.ln() / Decimal("1.0001").ln()) * 2
    guess = int(raw_tick.to_integral_value(rounding="ROUND_FLOOR"))

    # walk until correct range
    while get_sqrt_ratio_at_tick(guess + 1) <= sqrt_price_x96:
        guess += 1
    while get_sqrt_ratio_at_tick(guess) > sqrt_price_x96:
        guess -= 1
    return guess


# ---------------------- SqrtPriceMath (Uniswap core) ----------------------
def get_amount0_delta(liquidity: int, sqrt_a: int, sqrt_b: int, round_up: bool) -> int:
    """Token0 delta for price range [sqrt_a, sqrt_b)"""
    if sqrt_a > sqrt_b:
        sqrt_a, sqrt_b = sqrt_b, sqrt_a
    num = liquidity * (sqrt_b - sqrt_a) * Q96
    den = sqrt_b * sqrt_a
    if round_up:
        return (num + den - 1) // den
    else:
        return num // den


def get_amount1_delta(liquidity: int, sqrt_a: int, sqrt_b: int, round_up: bool) -> int:
    """Token1 delta for price range [sqrt_a, sqrt_b)"""
    if sqrt_a > sqrt_b:
        sqrt_a, sqrt_b = sqrt_b, sqrt_a
    diff = sqrt_b - sqrt_a
    if round_up:
        return (liquidity * diff + Q96 - 1) // Q96
    else:
        return liquidity * diff // Q96


def get_next_sqrt_price_from_input(sqrt_p: int, liquidity: int, amount_in: int, zero_for_one: bool) -> int:
    """
    Implements Uniswap's SqrtPriceMath.getNextSqrtPriceFromInput()
    """
    if zero_for_one:
        # token0 → token1: decreasing sqrtP
        product = amount_in * sqrt_p
        numerator = liquidity * Q96
        denominator = liquidity * Q96 + product
        return (numerator * sqrt_p + denominator - 1) // denominator
    else:
        # token1 → token0: increasing sqrtP
        delta = (amount_in * Q96 + liquidity - 1) // liquidity
        return sqrt_p + delta


# ---------------------- Fee helpers ----------------------
def apply_fee(amount_wo_fee: int, fee: int) -> int:
    """Convert pool-consumed amount → user-paid amount (with fee)"""
    return (amount_wo_fee * FEE_DENOM + (FEE_DENOM - fee - 1)) // (FEE_DENOM - fee)


def remove_fee(amount_with_fee: int, fee: int) -> int:
    """Convert user-paid amount (with fee) → pool-consumed amount (post-fee)"""
    return amount_with_fee * (FEE_DENOM - fee) // FEE_DENOM


# ---------------------- Exact Input Single ----------------------
def quote_exact_input_single(
    sqrt_price_x96: int,
    liquidity: int,
    tick_spacing: int,
    current_tick: int,
    exact_input_amount: int,
    fee: int,
    zero_for_one: bool,
    tick_bitmap: list[int] | None = None,
    initialized_ticks: list[int] | None = None
):
    """
    Pure math simulation of Uniswap V3 single-hop exactInput swap.
    - zero_for_one = True  => token0→token1
      (price decreases, sqrtP goes down)
    - zero_for_one = False => token1→token0
      (price increases, sqrtP goes up)
    """

    rem_in_with_fee = exact_input_amount
    rem_in = remove_fee(rem_in_with_fee, fee)
    out_total = 0
    sqrt_p = sqrt_price_x96
    tick = current_tick

    # sort ticks if given
    if initialized_ticks is not None:
        initialized_ticks = sorted(initialized_ticks)

    while rem_in > 0:
        if initialized_ticks is not None:
            # find next initialized tick
            next_tick_candidates = [t for t in initialized_ticks if (t > tick if not zero_for_one else t < tick)]
            if not next_tick_candidates:
                break
            next_tick = next_tick_candidates[0] if not zero_for_one else next_tick_candidates[-1]
            sqrt_target = get_sqrt_ratio_at_tick(next_tick)
        else:
            # fallback: just simulate small movement
            sqrt_target = sqrt_p + (Q96 // 1000000 if not zero_for_one else -(Q96 // 1000000))

        # how much input can move to next tick
        if zero_for_one:
            max_in = get_amount0_delta(liquidity, sqrt_target, sqrt_p, True)
        else:
            max_in = get_amount1_delta(liquidity, sqrt_p, sqrt_target, True)

        in_after_fee = rem_in

        if in_after_fee < max_in:
            # partial step inside tick
            new_sqrt_p = get_next_sqrt_price_from_input(sqrt_p, liquidity, in_after_fee, zero_for_one)
            if zero_for_one:
                out = get_amount1_delta(liquidity, new_sqrt_p, sqrt_p, False)
            else:
                out = get_amount0_delta(liquidity, sqrt_p, new_sqrt_p, False)
            sqrt_p = new_sqrt_p
            rem_in = 0
            out_total += out
            tick = get_tick_at_sqrt_ratio(sqrt_p)
        else:
            # cross full tick
            if zero_for_one:
                out = get_amount1_delta(liquidity, sqrt_target, sqrt_p, False)
            else:
                out = get_amount0_delta(liquidity, sqrt_p, sqrt_target, False)
            out_total += out
            rem_in -= max_in
            sqrt_p = sqrt_target
            tick = next_tick

    return {
        "amount_out": out_total,
        "final_sqrt_price_x96": sqrt_p,
        "final_tick": tick,
    }


# ---------------------- Example Test ----------------------
if __name__ == "__main__":
    # Example: token1→token0 swap
    sqrt_price = 2103983683516861075389684332587
    liquidity = 573754460235582
    tick = 65588
    fee = 3000
    input_amt = 6445123
    zero_for_one = False

    # test against example tick list (truncated)
    sorted_ticks = [39120, 39480, 39540, 40380, 40560, 40800, 41100, 76020, 78240, 88560, 89220, 90000]

    res = quote_exact_input_single(
        sqrt_price_x96=sqrt_price,
        liquidity=liquidity,
        tick_spacing=60,
        current_tick=tick,
        exact_input_amount=input_amt,
        fee=fee,
        zero_for_one=zero_for_one,
        initialized_ticks=sorted_ticks,
    )

    print("amount_out:", res["amount_out"])
    print("final_tick:", res["final_tick"])
    print("final_sqrt_price_x96:", res["final_sqrt_price_x96"])
