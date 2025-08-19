from web3 import Web3
from decimal import Decimal

from config import INFURA_API_KEY

# ---- config ----
PAIR_ADDR = Web3.to_checksum_address("0xdeae1ff5282d83aadd42f85c57f6e69a037bf7cd")

# Minimal ABIs
PAIR_ABI = [
  {"constant":True,"inputs":[],"name":"token0","outputs":[{"name":"","type":"address"}],"type":"function"},
  {"constant":True,"inputs":[],"name":"token1","outputs":[{"name":"","type":"address"}],"type":"function"},
  {"constant":True,"inputs":[],"name":"getReserves","outputs":[
      {"name":"_reserve0","type":"uint112"},
      {"name":"_reserve1","type":"uint112"},
      {"name":"_blockTimestampLast","type":"uint32"}],"type":"function"},
]

ERC20_ABI = [
  {"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},
  {"constant":True,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"type":"function"},
  {"constant":True,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"type":"function"},
]

# ---- connect ----
w3 = Web3(Web3.HTTPProvider(f"https://arbitrum-mainnet.infura.io/v3/{INFURA_API_KEY}"))
assert w3.is_connected(), "RPC not reachable"

pair = w3.eth.contract(address=PAIR_ADDR, abi=PAIR_ABI)

# token addresses
t0_addr = pair.functions.token0().call()
t1_addr = pair.functions.token1().call()

t0 = w3.eth.contract(address=t0_addr, abi=ERC20_ABI)
t1 = w3.eth.contract(address=t1_addr, abi=ERC20_ABI)

t0_dec = t0.functions.decimals().call()
t1_dec = t1.functions.decimals().call()
t0_sym = t0.functions.symbol().call()
t1_sym = t1.functions.symbol().call()

# ---- latest reserves ----
r0, r1, ts = pair.functions.getReserves().call()
r0_hr = Decimal(r0) / (Decimal(10) ** t0_dec)
r1_hr = Decimal(r1) / (Decimal(10) ** t1_dec)

print(f"Pair: {t0_sym}/{t1_sym}")
print(f"token0: {t0_addr}")
print(f"token1: {t1_addr}")
print(f"Reserves (raw): r0={r0}, r1={r1}, blockTimestampLast={ts}")
print(f"Reserves (human): {t0_sym}={r0_hr}, {t1_sym}={r1_hr}")

# implied spot prices from reserve ratio (ignoring fee/price impact):
# price of token0 in token1 units:
if r0 > 0:
    p0_in_1 = (Decimal(r1) / (Decimal(10) ** t1_dec)) / (Decimal(r0) / (Decimal(10) ** t0_dec))
    print(f"Price: 1 {t0_sym} ≈ {p0_in_1} {t1_sym}")
# price of token1 in token0 units:
if r1 > 0:
    p1_in_0 = (Decimal(r0) / (Decimal(10) ** t0_dec)) / (Decimal(r1) / (Decimal(10) ** t1_dec))
    print(f"Price: 1 {t1_sym} ≈ {p1_in_0} {t0_sym}")

# ---- historical query (optional) ----
# replace with a specific block number if you want a past state
block_number = w3.eth.block_number - 5000  # example: ~5000 blocks ago
r0_h, r1_h, ts_h = pair.functions.getReserves().call(block_identifier=block_number)
print(f"\nHistorical reserves @ block {block_number}: r0={r0_h}, r1={r1_h}, ts={ts_h}")
