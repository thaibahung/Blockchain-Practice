# save as fetch_sepolia_v2_pairs.py
import os
import csv
import math
from dotenv import load_dotenv
from web3 import Web3
from web3._utils.events import get_event_data
from typing import Optional, Dict, Any
from config import INFURA_API_KEY

load_dotenv()

SEPOLIA_RPC = f"https://sepolia.infura.io/v3/{INFURA_API_KEY}"

w3 = Web3(Web3.HTTPProvider(SEPOLIA_RPC))
print("Connected:", w3.is_connected())
FACTORY = Web3.to_checksum_address("0xc9f18c25Cfca2975d6eD18Fc63962EBd1083e978")

# Minimal ABIs we need
FACTORY_ABI = [{"inputs":[{"internalType":"address","name":"_feeToSetter","type":"address"}],"payable":False,"stateMutability":"nonpayable","type":"constructor"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"token0","type":"address"},{"indexed":True,"internalType":"address","name":"token1","type":"address"},{"indexed":False,"internalType":"address","name":"pair","type":"address"},{"indexed":False,"internalType":"uint256","name":"","type":"uint256"}],"name":"PairCreated","type":"event"},{"constant":True,"inputs":[],"name":"INIT_CODE_HASH","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[{"internalType":"uint256","name":"","type":"uint256"}],"name":"allPairs","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"allPairsLength","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":False,"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"}],"name":"createPair","outputs":[{"internalType":"address","name":"pair","type":"address"}],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":True,"inputs":[],"name":"feeTo","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"feeToSetter","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],"name":"getPair","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":False,"inputs":[{"internalType":"address","name":"_feeTo","type":"address"}],"name":"setFeeTo","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":False,"inputs":[{"internalType":"address","name":"_feeToSetter","type":"address"}],"name":"setFeeToSetter","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"}]

PAIR_ABI = [
    {"constant":True,"inputs":[],"name":"token0","outputs":[{"name":"","type":"address"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"token1","outputs":[{"name":"","type":"address"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"getReserves","outputs":[
        {"internalType":"uint112","name":"_reserve0","type":"uint112"},
        {"internalType":"uint112","name":"_reserve1","type":"uint112"},
        {"internalType":"uint32","name":"_blockTimestampLast","type":"uint32"}
    ],"type":"function"}
]

ERC20_ABI = [
    {"constant":True,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"type":"function"},
]

factory = w3.eth.contract(address=FACTORY, abi=FACTORY_ABI)
pair_event_abi = next(a for a in FACTORY_ABI if a.get("name")=="PairCreated")
event_signature_text = "PairCreated(address,address,address,uint256)"
event_topic = "0x" + w3.keccak(text=event_signature_text).hex()
print("Event topic:", event_topic, "len:", len(event_topic))

# block range settings (adjust start_block as needed)
current = w3.eth.block_number
start_block = 	4014311           # or a known factory deployment block
end_block = start_block + 50000             # or current
chunk = 50_000            # chunk size - adjust to avoid timeouts (smaller for slow nodes)
min_reserve_threshold = 1  # numeric threshold in token units (not USD); set per-pair test

pairs = {}

print("Scanning blocks", start_block, "to", end_block)
for from_block in range(start_block, end_block + 1, chunk):
    to_block = min(end_block, from_block + chunk - 1)
    print("Querying logs", from_block, "->", to_block)
    try:
        logs = w3.eth.get_logs({
            "fromBlock": from_block,
            "toBlock": to_block,
            "address": FACTORY,
            "topics": [event_topic]
        })
    except Exception as e:
        print("get_logs error:", e)
        continue

    for log in logs:
        try:
            ev = get_event_data(w3.codec, pair_event_abi, log)
            token0 = ev["args"]["token0"]
            token1 = ev["args"]["token1"]
            pair = ev["args"]["pair"]
            pair = Web3.to_checksum_address(pair)
            token0 = Web3.to_checksum_address(token0)
            token1 = Web3.to_checksum_address(token1)
            pairs[pair] = {"token0": token0, "token1": token1, "block": log["blockNumber"]}
        except Exception as e:
            print("decode event err:", e)

print(f"Found {len(pairs)} pairs from logs")

# Enrich pairs: get reserves, token symbols/decimals
def safe_call(contract, fn_name):
    try:
        return getattr(contract.functions, fn_name)().call()
    except Exception:
        return None

token_cache = {}

def get_token_info(addr):
    if addr in token_cache:
        return token_cache[addr]
    contract = w3.eth.contract(address=addr, abi=ERC20_ABI)
    sym = safe_call(contract, "symbol") or ""
    dec = safe_call(contract, "decimals") or 18
    token_cache[addr] = (sym, dec)
    return sym, dec

enriched = []
for i, (pair_addr, info) in enumerate(pairs.items()):
    if i % 50 == 0:
        print(f"Processing pair {i}/{len(pairs)}")

    pair_contract = w3.eth.contract(address=pair_addr, abi=PAIR_ABI)
    reserves = safe_call(pair_contract, "getReserves")

    t0 = info["token0"]
    t1 = info["token1"]
    sym0, dec0 = get_token_info(t0)
    sym1, dec1 = get_token_info(t1)

    reserve0 = reserve1 = None
    if reserves:
        reserve0, reserve1, _ = reserves

    # Filter by minimal liquidity
    has_liq = False
    if reserve0 is not None and reserve1 is not None:
        human_r0 = reserve0 / (10 ** dec0)
        human_r1 = reserve1 / (10 ** dec1)
        if human_r0 >= min_reserve_threshold or human_r1 >= min_reserve_threshold:
            has_liq = True
    
    if has_liq == False:
        continue  # skip pairs without sufficient liquidity

    row = {
        "pair": pair_addr,
        "token0": t0,
        "token1": t1,
        "symbol0": sym0,
        "symbol1": sym1,
        "has_liq": has_liq,
    }

    # Append immediately to CSV
    with open("pools_sepolia_v2.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        writer.writerow(row)