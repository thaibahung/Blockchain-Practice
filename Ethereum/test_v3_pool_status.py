from web3 import Web3
import asyncio

w3 = Web3(Web3.LegacyWebSocketProvider("wss://mainnet.infura.io/ws/v3/67d4fda1bfc248aaba4b1ac954169e08"))
POOL_V3 = Web3.to_checksum_address("0x3733493ec5d2c181dcd7c54ed100641c0f07bb0e") 

# Minimal V3 ABI fragments
V3_ABI = [
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
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "liquidity",
        "outputs": [{"internalType":"uint128","name":"","type":"uint128"}],
        "stateMutability": "view",
        "type": "function"
    },
    # Optional: subscribe to Swap events
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True,"internalType":"address","name":"sender","type":"address"},
            {"indexed": False,"internalType":"int256","name":"amount0","type":"int256"},
            {"indexed": False,"internalType":"int256","name":"amount1","type":"int256"},
            {"indexed": False,"internalType":"uint160","name":"sqrtPriceX96","type":"uint160"},
            {"indexed": False,"internalType":"uint128","name":"liquidity","type":"uint128"},
            {"indexed": False,"internalType":"int24","name":"tick","type":"int24"}
        ],
        "name": "Swap",
        "type": "event"
    }
]

pool = w3.eth.contract(address=POOL_V3, abi=V3_ABI)

async def poll_v3(interval=5):
    while True:
        spx96, tick, *_ = pool.functions.slot0().call()
        liq = pool.functions.liquidity().call()
        print(f"[Pull] √PriceX96={spx96}, tick={tick}, liquidity={liq}")
        await asyncio.sleep(interval)

asyncio.run(poll_v3())
