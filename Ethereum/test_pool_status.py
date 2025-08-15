from web3 import Web3
import asyncio

# 1) Connect over WebSockets so we can both call and subscribe
w3 = Web3(Web3.LegacyWebSocketProvider("wss://mainnet.infura.io/ws/v3/67d4fda1bfc248aaba4b1ac954169e08"))

# 2) Pool address and minimal ABI for V2
POOL = Web3.to_checksum_address("0x03b59bd1c8b9f6c265ba0c3421923b93f15036fa")  # example: Uniswap V2 factory
V2_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"internalType": "uint112","name": "_reserve0","type": "uint112"},
            {"internalType": "uint112","name": "_reserve1","type": "uint112"},
            {"internalType": "uint32","name": "_blockTimestampLast","type": "uint32"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False,"internalType": "uint112","name": "reserve0","type": "uint112"},
            {"indexed": False,"internalType": "uint112","name": "reserve1","type": "uint112"}
        ],
        "name": "Sync",
        "type": "event"
    }
]

contract = w3.eth.contract(address=POOL, abi=V2_ABI)

async def poll_reserves(interval=5):
    while True:
        r0, r1, ts = contract.functions.getReserves().call()
        print(f"[Pull] Reserves: {r0} / {r1} (last update {ts})")
        await asyncio.sleep(interval)

# Kick off a simple pull loop
asyncio.run(poll_reserves())
