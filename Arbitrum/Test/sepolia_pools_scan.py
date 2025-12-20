# save as fetch_sepolia_v3_pools.py
import os
import csv
from dotenv import load_dotenv
from web3 import Web3
from web3._utils.events import get_event_data

load_dotenv()

SEPOLIA_RPC = "https://arbitrum-sepolia.infura.io/v3/15495e8f0e6b481b8ee269ebc6a5a58e"

w3 = Web3(Web3.HTTPProvider(SEPOLIA_RPC))
print("Connected:", w3.is_connected())

# Uniswap V3 factory on Arbitrum Sepolia
FACTORY = Web3.to_checksum_address("0x248AB79Bbb9bC29bB72f7Cd42F17e054Fc40188e")

# Minimal V3 factory ABI (taken from your source)
FACTORY_ABI = [
    {"inputs":[],"stateMutability":"nonpayable","type":"constructor"},
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True,"internalType":"uint24","name":"fee","type":"uint24"},
            {"indexed": True,"internalType":"int24","name":"tickSpacing","type":"int24"}
        ],
        "name": "FeeAmountEnabled",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True,"internalType":"address","name":"oldOwner","type":"address"},
            {"indexed": True,"internalType":"address","name":"newOwner","type":"address"}
        ],
        "name": "OwnerChanged",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True,"internalType":"address","name":"token0","type":"address"},
            {"indexed": True,"internalType":"address","name":"token1","type":"address"},
            {"indexed": True,"internalType":"uint24","name":"fee","type":"uint24"},
            {"indexed": False,"internalType":"int24","name":"tickSpacing","type":"int24"},
            {"indexed": False,"internalType":"address","name":"pool","type":"address"},
        ],
        "name": "PoolCreated",
        "type": "event"
    },
    {
        "inputs":[
            {"internalType":"address","name":"tokenA","type":"address"},
            {"internalType":"address","name":"tokenB","type":"address"},
            {"internalType":"uint24","name":"fee","type":"uint24"}
        ],
        "name":"createPool",
        "outputs":[{"internalType":"address","name":"pool","type":"address"}],
        "stateMutability":"nonpayable",
        "type":"function"
    },
    {
        "inputs":[{"internalType":"uint24","name":"fee","type":"uint24"},
                  {"internalType":"int24","name":"tickSpacing","type":"int24"}],
        "name":"enableFeeAmount",
        "outputs":[],
        "stateMutability":"nonpayable",
        "type":"function"
    },
    {
        "inputs":[{"internalType":"uint24","name":"","type":"uint24"}],
        "name":"feeAmountTickSpacing",
        "outputs":[{"internalType":"int24","name":"","type":"int24"}],
        "stateMutability":"view",
        "type":"function"
    },
    {
        "inputs":[
            {"internalType":"address","name":"","type":"address"},
            {"internalType":"address","name":"","type":"address"},
            {"internalType":"uint24","name":"","type":"uint24"}
        ],
        "name":"getPool",
        "outputs":[{"internalType":"address","name":"","type":"address"}],
        "stateMutability":"view",
        "type":"function"
    },
    {
        "inputs":[],"name":"owner",
        "outputs":[{"internalType":"address","name":"","type":"address"}],
        "stateMutability":"view",
        "type":"function"
    },
    {
        "inputs":[{"internalType":"address","name":"_owner","type":"address"}],
        "name":"setOwner",
        "outputs":[],
        "stateMutability":"nonpayable",
        "type":"function"
    }
]

# Minimal Uniswap V3 pool ABI pieces we care about
POOL_ABI = [
    {"inputs":[],"name":"token0","outputs":[{"internalType":"address","name":"","type":"address"}],
     "stateMutability":"view","type":"function"},
    {"inputs":[],"name":"token1","outputs":[{"internalType":"address","name":"","type":"address"}],
     "stateMutability":"view","type":"function"},
    {"inputs":[],"name":"fee","outputs":[{"internalType":"uint24","name":"","type":"uint24"}],
     "stateMutability":"view","type":"function"},
    {"inputs":[],"name":"liquidity","outputs":[{"internalType":"uint128","name":"","type":"uint128"}],
     "stateMutability":"view","type":"function"},
    # slot0 is optional; useful if you later want to estimate reserves from sqrtPriceX96
    {
        "inputs": [],
        "name": "slot0",
        "outputs": [
            {"internalType":"uint160","name":"sqrtPriceX96","type":"uint160"},
            {"internalType":"int24","name":"tick","type":"int24"},
            {"internalType":"uint16","name":"observationIndex","type":"uint16"},
            {"internalType":"uint16","name":"observationCardinality","type":"uint16"},
            {"internalType":"uint16","name":"observationCardinalityNext","type":"uint16"},
            {"internalType":"uint8","name":"feeProtocol","type":"uint8"},
            {"internalType":"bool","name":"unlocked","type":"bool"}
        ],
        "stateMutability":"view",
        "type":"function"
    }
]

ERC20_ABI = [
    {"constant":True,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"type":"function"},
]

factory = w3.eth.contract(address=FACTORY, abi=FACTORY_ABI)
pool_event_abi = next(a for a in FACTORY_ABI if a.get("name") == "PoolCreated")

# Event signature: PoolCreated(address,address,uint24,int24,address)
event_signature_text = "PoolCreated(address,address,uint24,int24,address)"
event_topic = "0x" + w3.keccak(text=event_signature_text).hex()
print("Event topic:", event_topic, "len:", len(event_topic))

# Block range settings (adjust start_block as needed)
current = w3.eth.block_number
start_block = 222693704       # factory deployment block (your value)
end_block   = start_block + 20_000_00  # adjust as you like
chunk       = 500_000          # chunk size
min_liquidity_threshold = 0    # require liquidity > this (uint128)

pools = {}

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
            ev = get_event_data(w3.codec, pool_event_abi, log)
            token0 = Web3.to_checksum_address(ev["args"]["token0"])
            token1 = Web3.to_checksum_address(ev["args"]["token1"])
            fee    = ev["args"]["fee"]        # uint24
            pool   = Web3.to_checksum_address(ev["args"]["pool"])
            pools[pool] = {
                "token0": token0,
                "token1": token1,
                "fee": fee,
                "block": log["blockNumber"],
            }
        except Exception as e:
            print("decode event err:", e)

print(f"Found {len(pools)} pools from logs")

# Enrich pools: token symbols/decimals and liquidity
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

# If you want a header row, create the file and write header once:
csv_path = "pools_sepolia_v3.csv"
if not os.path.exists(csv_path):
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "pool", "token0", "token1", "symbol0", "symbol1",
            "fee", "liquidity", "block"
        ])
        writer.writeheader()

for i, (pool_addr, info) in enumerate(pools.items()):
    if i % 50 == 0:
        print(f"Processing pool {i}/{len(pools)}")

    pool_contract = w3.eth.contract(address=pool_addr, abi=POOL_ABI)

    liquidity = safe_call(pool_contract, "liquidity")  # uint128
    if liquidity is None:
        liquidity = 0

    # simple filter: require some liquidity
    if liquidity <= min_liquidity_threshold:
        continue

    t0 = info["token0"]
    t1 = info["token1"]
    sym0, _ = get_token_info(t0)
    sym1, _ = get_token_info(t1)

    row = {
        "pool": pool_addr,
        "token0": t0,
        "token1": t1,
        "symbol0": sym0,
        "symbol1": sym1,
        "fee": info["fee"],
        "liquidity": int(liquidity),
        "block": info["block"],
    }

    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        writer.writerow(row)

print("Done. Saved pools to", csv_path)
