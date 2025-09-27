#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
One-month Optimistic MEV metrics on Arbitrum from a date range.

Outputs (printed at the end):
  - avg_revert_fee_eth: mean fee (ETH) of reverted cyclicArb txs
  - avg_profit_weth:    mean WETH profit of successful cyclic cyclicArb trades

Usage example:
  python arb_mev_metrics_month.py \
      --rpc https://arb-mainnet.g.alchemy.com/v2/YOUR_KEY \
      --from-date 2025-08-01T00:00:00Z \
      --to-date   2025-09-01T00:00:00Z \
      --chunk-blocks 100000
"""
import argparse, datetime as dt, math
from collections import defaultdict, namedtuple
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Set, Any

from web3 import Web3
from eth_abi import decode as abi_decode

# ---------- Config: routers / aggregators (α1 filter; extend as needed) ----------
ROUTERS = {
    "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45",  # Uniswap V3 universal
    "0xe592427a0aece92de3edee1f18e0157c05861564",  # Uniswap V3 exactInputSingle
    "0x1b02da8cb0d097eb8d57a175b88c7d8b47997506",  # Sushi v2
    "0xc873fecbd354f5a56e00e710b90ef4201db2448d",  # Camelot v2-like
    "0xaa0c3f5f7dfdad62a9d605f3c2c7293c7b1598a5",  # Ramses router (example)
}
AGGREGATORS = {
    "0x1111111254eeb25477b68fb85ed929f73a960582",  # 1inch
    "0xdef1c0ded9bec7f1a1670819833240f027b25eff",  # 0x (may vary per chain)
}

# WETH on Arbitrum
WETH = Web3.to_checksum_address("0x82af49447d8a07e3bd95bd0d56f35241523fbab1")

# ---------- Minimal ABIs & topics ----------
ERC20_ABI = [
    {"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"type":"function"}
]
UNIV2_PAIR_ABI = [
    {"constant":True,"inputs":[],"name":"token0","outputs":[{"name":"","type":"address"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"token1","outputs":[{"name":"","type":"address"}],"type":"function"},
]
UNIV3_POOL_ABI = [
    {"constant":True,"inputs":[],"name":"token0","outputs":[{"name":"","type":"address"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"token1","outputs":[{"name":"","type":"address"}],"type":"function"},
]

UNIV2_SWAP_TOPIC = Web3.keccak(text="Swap(address,address,uint256,uint256,uint256,uint256,address)")
UNIV3_SWAP_TOPIC = Web3.keccak(text="Swap(address,address,int256,int256,uint160,uint128,int24)")

SwapEvt = namedtuple("SwapEvt", "txh block li pool kind token_in token_out amount_in amount_out")

def cs(x: Optional[str]) -> Optional[str]:
    return Web3.to_checksum_address(x) if x else x

@dataclass
class Chain:
    w3: Web3
    erc_cache: Dict[str, Dict[str, Any]]
    pool_tokens: Dict[Tuple[str,str], Tuple[str,str]]
    def __init__(self, w3: Web3):
        self.w3 = w3
        self.erc_cache = {}
        self.pool_tokens = {}
    def token0_token1(self, pool: str, kind: str) -> Tuple[str,str]:
        key = (pool, kind)
        if key in self.pool_tokens:
            return self.pool_tokens[key]
        abi = UNIV2_PAIR_ABI if kind=="v2" else UNIV3_POOL_ABI
        c = self.w3.eth.contract(address=pool, abi=abi)
        t0 = cs(c.functions.token0().call())
        t1 = cs(c.functions.token1().call())
        self.pool_tokens[key] = (t0, t1)
        return t0, t1
    def decimals(self, token: str) -> int:
        token = cs(token)
        if token in self.erc_cache and "decimals" in self.erc_cache[token]:
            return self.erc_cache[token]["decimals"]
        c = self.w3.eth.contract(address=token, abi=ERC20_ABI)
        try:
            d = c.functions.decimals().call()
        except Exception:
            d = 18
        self.erc_cache.setdefault(token, {})["decimals"] = d
        return d

# ---------- Date → block helpers ----------
def parse_iso(ts: str) -> int:
    # returns POSIX seconds (UTC)
    if ts.endswith("Z"): ts = ts[:-1]
    return int(dt.datetime.fromisoformat(ts).replace(tzinfo=dt.timezone.utc).timestamp())

def get_block_at_or_after(w3: Web3, ts_sec: int, search_start: Optional[int]=None, search_end: Optional[int]=None) -> int:
    """
    Binary search the block whose timestamp >= ts_sec (first block at/after time).
    """
    head = w3.eth.block_number
    lo = 1 if search_start is None else max(1, search_start)
    hi = head if search_end is None else min(head, search_end)
    # narrow bounds quickly: assume ~1 block/sec
    b_hi = w3.eth.get_block(hi)
    if b_hi.timestamp < ts_sec:
        return hi  # past head; best effort
    b_lo = w3.eth.get_block(lo)
    if b_lo.timestamp >= ts_sec:
        return lo
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        tm = w3.eth.get_block(mid).timestamp
        if tm >= ts_sec:
            hi = mid
        else:
            lo = mid
    return hi

# ---------- Swap log scanning (chunked) ----------
def fetch_swaps_chunk(w3: Web3, chain: Chain, b0: int, b1: int) -> Dict[str, List[SwapEvt]]:
    swaps_by_tx: Dict[str, List[SwapEvt]] = defaultdict(list)
    print(f"get_logs filter: fromBlock={b0}, toBlock={b1}, topics={[UNIV2_SWAP_TOPIC, UNIV3_SWAP_TOPIC]}")
    logs = w3.eth.get_logs({
        "fromBlock": b0,
        "toBlock": b1,
        "topics": [[UNIV2_SWAP_TOPIC, UNIV3_SWAP_TOPIC]]
    })
    print(f"Fetched {len(logs)} logs")
    for lg in logs:
        topic0 = lg["topics"][0]
        pool = cs(lg["address"])
        txh = lg["transactionHash"].hex()
        block = lg["blockNumber"]; li = lg["logIndex"]
        if topic0 == UNIV2_SWAP_TOPIC:
            a0in,a1in,a0out,a1out = decode_or_skip(["uint256","uint256","uint256","uint256"], lg["data"])
            if a0in is None: continue
            t0,t1 = chain.token0_token1(pool, "v2")
            if a0in > 0:
                tin, ain = t0, a0in
                tout, aout = t1, a1out
            else:
                tin, ain = t1, a1in
                tout, aout = t0, a0out
            swaps_by_tx[txh].append(SwapEvt(txh, block, li, pool, "v2", tin, tout, int(ain), int(aout)))
        else:
            a0,a1,_,_,_ = decode_or_skip(["int256","int256","uint160","uint128","int24"], lg["data"])
            if a0 is None: continue
            t0,t1 = chain.token0_token1(pool, "v3")
            if a0 > 0:
                tin, ain = t0, a0
                tout, aout = t1, -a1
            else:
                tin, ain = t1, a1
                tout, aout = t0, -a0
            swaps_by_tx[txh].append(SwapEvt(txh, block, li, pool, "v3", tin, tout, int(ain), int(aout)))
    for txh in swaps_by_tx:
        swaps_by_tx[txh].sort(key=lambda s: s.li)
    return swaps_by_tx

def decode_or_skip(types: List[str], data_hex: str):
    try:
        return abi_decode(types, bytes(data_hex))
    except Exception:
        return (None,) * len(types)

# ---------- Cycle building & ΔB ----------
def build_cycle(swaps: List[SwapEvt]):
    if len(swaps) < 2:
        return False, [], {}
    path = []
    cont = True
    for i, s in enumerate(swaps):
        sold = cs(s.token_in); bought = cs(s.token_out)
        if i == 0:
            path.extend([sold, bought])
        else:
            if path[-1] != sold:
                cont = False; break
            path.append(bought)
    if (not cont) or (path[0] != path[-1]):
        return False, path, {}
    delta = defaultdict(int)
    for s in swaps:
        delta[cs(s.token_out)] += int(s.amount_out)
        delta[cs(s.token_in)]  -= int(s.amount_in)
    return True, path, dict(delta)

def passes_profit(delta: Dict[str,int]) -> bool:
    if not delta: return False
    any_pos = False
    for v in delta.values():
        if v < 0: return False
        if v > 0: any_pos = True
    return any_pos

# ---------- Stage-1 seeding per chunk ----------
def seed_cbot_for_swaps(w3: Web3, swaps_by_tx: Dict[str, List[SwapEvt]]) -> Set[str]:
    cbot = set()
    ROUTERS_LC = {a.lower() for a in ROUTERS}
    AGGS_LC    = {a.lower() for a in AGGREGATORS}
    for txh, swaps in swaps_by_tx.items():
        try:
            tx = w3.eth.get_transaction(txh)
        except Exception:
            continue
        to_addr = (tx["to"] or "").lower()
        if not to_addr:
            continue
        if to_addr in ROUTERS_LC or to_addr in AGGS_LC:
            continue
        ok, path, delta = build_cycle(swaps)
        if not ok: continue
        if not passes_profit(delta): continue
        cbot.add(Web3.to_checksum_address(to_addr))
    return cbot

# ---------- Stage-2 labeling & metrics per chunk ----------
def measure_chunk(w3: Web3, chain: Chain, b0: int, b1: int, cbot: Set[str]) -> Tuple[List[float], List[float]]:
    # revert fees (ETH), profits (WETH)
    revert_fees_eth: List[float] = []
    profits_weth: List[float] = []

    # gather swaps once for profit calc
    swaps_by_tx = fetch_swaps_chunk(w3, chain, b0, b1)
    tx_with_swaps = set(swaps_by_tx.keys())

    cbot_lc = {a.lower() for a in cbot}

    for b in range(b0, b1+1):
        try:
            blk = w3.eth.get_block(b, full_transactions=True)
        except Exception:
            continue
        for tx in blk["transactions"]:
            to_addr = (tx["to"] or "").lower()
            if not to_addr:  # skip creations
                continue
            if to_addr not in cbot_lc:
                continue  # only measure cyclicArb purpose
            txh = tx["hash"].hex()
            try:
                r = w3.eth.get_transaction_receipt(txh)
            except Exception:
                continue

            egp = r.get("effectiveGasPrice", tx.get("gasPrice", 0)) or 0
            l1  = r.get("l1Fee", 0) or 0
            fee_eth = (r["gasUsed"] * int(egp) + int(l1)) / 1e18

            if r["status"] != 1:
                revert_fees_eth.append(fee_eth)
                continue

            # success: compute ΔB → WETH profit if any
            if txh in tx_with_swaps:
                ok, path, delta = build_cycle(swaps_by_tx[txh])
                if ok and delta:
                    v = delta.get(WETH, 0)
                    if v > 0:
                        dec = chain.decimals(WETH)
                        profits_weth.append(v / (10**dec))
    return revert_fees_eth, profits_weth

# ---------- Orchestration ----------
def run_month(w3: Web3, from_ts: int, to_ts: int, chunk_blocks: int):
    chain = Chain(w3)

    # Resolve date → block numbers
    start_block = get_block_at_or_after(w3, from_ts)
    end_block   = get_block_at_or_after(w3, to_ts)
    if end_block < start_block:
        start_block, end_block = end_block, start_block

    print(f"[Blocks] {start_block} → {end_block}  (~{end_block - start_block + 1} blocks)")

    # Stage-1: seed C_bot across the whole month, but done incrementally per chunk
    cbot: Set[str] = set()
    # First pass to collect swaps and seed bots across the month
    b0 = start_block
    while b0 <= end_block:
        b1 = min(end_block, b0 + chunk_blocks - 1)
        swaps = fetch_swaps_chunk(w3, chain, b0, b1)
        print(f"  Found {sum(len(v) for v in swaps.values())} swaps in chunk [{b0}-{b1}]")
        cbot |= seed_cbot_for_swaps(w3, swaps)
        print(f"  Seed pass: [{b0}-{b1}]  C_bot now {len(cbot)}")
        b0 = b1 + 1

    # Stage-2: measure per chunk
    all_reverts: List[float] = []
    all_profits: List[float] = []
    b0 = start_block
    while b0 <= end_block:
        b1 = min(end_block, b0 + chunk_blocks - 1)
        rev, prof = measure_chunk(w3, chain, b0, b1, cbot)
        all_reverts.extend(rev)
        all_profits.extend(prof)
        print(f"  Measure pass: [{b0}-{b1}]  +{len(rev)} reverts, +{len(prof)} profits")
        b0 = b1 + 1

    avg_revert = sum(all_reverts) / len(all_reverts) if all_reverts else 0.0
    avg_profit = sum(all_profits) / len(all_profits) if all_profits else 0.0

    return {
        "blocks_start": start_block,
        "blocks_end": end_block,
        "cbot": len(cbot),
        "revert_samples": len(all_reverts),
        "profit_samples": len(all_profits),
        "avg_revert_fee_eth": avg_revert,
        "avg_profit_weth": avg_profit,
    }

# ---------- CLI ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rpc", required=True, help="Arbitrum HTTPS RPC")
    ap.add_argument("--from-date", required=True, help="ISO8601, e.g. 2025-08-20T00:00:00Z")
    ap.add_argument("--to-date",   required=True, help="ISO8601, e.g. 2025-09-01T00:00:00Z")
    ap.add_argument("--chunk-blocks", type=int, default=100000, help="Block range per chunk (default 100k)")
    args = ap.parse_args()

    w3 = Web3(Web3.HTTPProvider(args.rpc, request_kwargs={"timeout": 180}))
    assert w3.is_connected(), "RPC not reachable"

    from_ts = parse_iso(args.from_date)
    to_ts   = parse_iso(args.to_date)

    stats = run_month(w3, from_ts, to_ts, args.chunk_blocks)

    print("\n=== Optimistic MEV (Arbitrum) — Monthly Metrics ===")
    print(f"Blocks: {stats['blocks_start']} → {stats['blocks_end']}")
    print(f"Seeded C_bot contracts: {stats['cbot']}")
    print(f"Reverted cyclicArb txs: {stats['revert_samples']}")
    print(f"Profitable cyclicArb trades (WETH+): {stats['profit_samples']}")
    print(f"\n(1) Average revert fee (ETH): {stats['avg_revert_fee_eth']:.10f}")
    print(f"(2) Average profit (WETH):    {stats['avg_profit_weth']:.10f}\n")

if __name__ == "__main__":
    main()
