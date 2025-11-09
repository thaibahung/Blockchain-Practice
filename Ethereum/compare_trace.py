import json
from decimal import Decimal, getcontext

getcontext().prec = 60  # high precision for sqrtPriceX96 math

getcontext().prec = 100  # enough precision for Uniswap math

Q96 = 2**96
FEE_DENOM = 1_000_000  # same as Uniswap denominator

# field map: from log index -> readable key
field_names = {
    "0": "stepIndex",
    "1": "currentTick",
    "2": "curSqrtP",
    "3": "nextTick",
    "4": "boundarySqrtP",
    "5": "liquidity",
    "6": "inBeforeFee",
    "7": "inAfterFee",
    "8": "maxInHere",
    "9": "isPartial",
    "10": "newSqrtP",
    "11": "inConsumed",
    "12": "outProduced",
    "13": "remInAfter",
    "14": "liquidityAfter",
    "15": "tickAfter",
}

# === Load on-chain trace ===
with open("trace_sepolia.json", "r") as f:
    raw = json.load(f)

onchain = []
for ev in raw:
    args = ev["args"]
    flat = {field_names[k]: args[k] for k in args if k in field_names}
    onchain.append(flat)

# === Example Python simulator (replace with your real step sim) ===
def simulate_step(state):
    """
    Replicates the Solidity _step() logic from RealTest.
    Inputs come from StepTrace (on-chain trace JSON).
    """
    # convert numeric fields
    cur_tick = int(state["currentTick"])
    cur_sqrtP = int(state["curSqrtP"])
    next_tick = int(state["nextTick"])
    boundary_sqrtP = int(state["boundarySqrtP"])
    L = int(state["liquidity"])
    in_before_fee = int(state["inBeforeFee"])
    in_after_fee = int(state["inAfterFee"])
    max_in_here = int(state["maxInHere"])
    is_partial = bool(state["isPartial"])
    fee = 3000  # replace if your pool’s fee tier differs

    # --- Helper math functions (Python analogs of Solidity libs) ---

    def get_amount0_delta(sa, sb, L, round_up):
        num = L * (sb - sa) * Q96
        den = sb * sa
        return (num + den - 1) // den if round_up else num // den

    def get_amount1_delta(sa, sb, L, round_up):
        diff = sb - sa
        num = L * diff
        return (num + Q96 - 1) // Q96 if round_up else num // Q96

    def apply_fee(amount_wo_fee):
        num = amount_wo_fee * FEE_DENOM
        den = FEE_DENOM - fee
        return (num + den - 1) // den

    def remove_fee(amount_with_fee):
        return (amount_with_fee * (FEE_DENOM - fee)) // FEE_DENOM

    # --- Core simulation ---

    ns = dict(state)  # new state (copy)
    out_delta = 0

    # If input (after fee) >= maxInHere ⇒ full step
    if in_after_fee >= max_in_here:
        # full step (cross tick)
        out_delta = get_amount0_delta(cur_sqrtP, boundary_sqrtP, L, False)

        # Update state (similar to Solidity’s ns)
        ns["remInAfter"] = str(
            in_before_fee - (max_in_here * FEE_DENOM // (FEE_DENOM - fee))
        )
        ns["newSqrtP"] = str(boundary_sqrtP)
        ns["tickAfter"] = str(next_tick)
        ns["liquidityAfter"] = str(L)
        ns["inConsumed"] = str(max_in_here)
        ns["outProduced"] = str(out_delta)

    else:
        # partial step (stop inside current tick)
        delta_sp_num = in_after_fee * Q96
        delta_sp_den = L
        delta_sp = -(-delta_sp_num // delta_sp_den)  # exact ceil division
        new_sqrt = cur_sqrtP + delta_sp

        out_delta = get_amount0_delta(cur_sqrtP, new_sqrt, L, False)

        ns["remInAfter"] = "0"
        ns["newSqrtP"] = str(new_sqrt)
        ns["tickAfter"] = str(cur_tick)
        ns["liquidityAfter"] = str(L)
        ns["inConsumed"] = str(in_after_fee)
        ns["outProduced"] = str(out_delta)

    return ns

# === Compare ===
for i, ev in enumerate(onchain):
    sim = simulate_step(ev)
    print(f"\nStep {i}:")
    for k in ev:
        val_on = ev[k]
        val_py = sim[k]
        if isinstance(val_on, str) and val_on.isdigit():
            val_on = Decimal(val_on)
            val_py = Decimal(val_py)
        if val_on != val_py:
            diff = abs(val_on - val_py) if isinstance(val_on, Decimal) else ""
            print(f"  ❌ {k}: chain={val_on}  sim={val_py}  diff={diff}")
        else:
            print(f"  ✅ {k}: {val_on}")
