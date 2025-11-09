from web3 import Web3
import csv
from config import INFURA_API_KEY
import time

SEPOLIA_RPC = f"https://sepolia.infura.io/v3/{INFURA_API_KEY}"
FACTORY_ADDR = "0xF62c03E08ada871A0bEb309762E260a7a6a880E6"

w3 = Web3(Web3.HTTPProvider(SEPOLIA_RPC))

FACTORY_ABI = [
    {"constant": True, "inputs": [], "name": "allPairsLength", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "name": "allPairs", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
]

PAIR_ABI = [
    {"constant": True, "inputs": [], "name": "token0", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [], "name": "token1", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [], "name": "getReserves", "outputs": [
        {"internalType": "uint112", "name": "_reserve0", "type": "uint112"},
        {"internalType": "uint112", "name": "_reserve1", "type": "uint112"},
        {"internalType": "uint32", "name": "_blockTimestampLast", "type": "uint32"}
    ], "stateMutability": "view", "type": "function"}
]

ERC20_ABI = [
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "stateMutability": "view", "type": "function"},
]

factory = w3.eth.contract(address=FACTORY_ADDR, abi=FACTORY_ABI)

# Get total pair count
total_pairs = 100
print(f"Total pairs: {total_pairs}")

# --- Start CSV ---
csv_file = open("pools_sepolia_v2.csv", "w", newline="", encoding="utf-8")
writer = csv.writer(csv_file)
writer.writerow(["pair", "token0", "symbol0", "token1", "symbol1", "reserve0", "reserve1"])

def safe_call(fn, default=None):
    try:
        return fn.call()
    except Exception:
        return default

for i in range(total_pairs):
    if i % 10 == 0:
        print(f"Processing {i}/{total_pairs}")

    pair_addr = factory.functions.allPairs(i).call()
    pair = w3.eth.contract(address=pair_addr, abi=PAIR_ABI)

    token0 = safe_call(pair.functions.token0)
    token1 = safe_call(pair.functions.token1)
    reserves = safe_call(pair.functions.getReserves)

    if not token0 or not token1 or not reserves:
        continue

    r0, r1, _ = reserves
    if r0 == 0 and r1 == 0:
        continue  # skip zero liquidity

    token0_contract = w3.eth.contract(address=token0, abi=ERC20_ABI)
    token1_contract = w3.eth.contract(address=token1, abi=ERC20_ABI)

    sym0 = safe_call(token0_contract.functions.symbol, "UNK0")
    sym1 = safe_call(token1_contract.functions.symbol, "UNK1")

    writer.writerow([pair_addr, token0, sym0, token1, sym1, r0, r1])
    csv_file.flush()  # ensure immediate write

    time.sleep(0.05)  # polite delay

csv_file.close()
print("✅ Done. Saved as sepolia_v2_liquid_pairs.csv")
