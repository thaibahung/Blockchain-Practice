import asyncio
import websockets
import json
import time
from web3 import Web3

Infura_wss = 'wss://mainnet.infura.io/ws/v3/67d4fda1bfc248aaba4b1ac954169e08'
QuickNode_wss = "wss://wiser-dark-theorem.quiknode.pro/6616c8f18079c8fc568bab2c163a6dba439d5c9f"
w3 = Web3(Web3.HTTPProvider("https://mainnet.infura.io/v3/67d4fda1bfc248aaba4b1ac954169e08"))

# Uniswap ETH/USDC Pair Address
UNISWAP_PAIR_ETH_USDC = "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc"

# Uniswap Pair ABI (Only `getReserves()` function)
UNISWAP_PAIR_ABI = """
[
    {
        "constant": true,
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"name": "_reserve0", "type": "uint112"},
            {"name": "_reserve1", "type": "uint112"},
            {"name": "_blockTimestampLast", "type": "uint32"}
        ],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    }
]
"""

# Uniswap Sync Event Signature (Keccak-256 Hash of `Sync(uint112,uint112)`)
SYNC_EVENT_SIGNATURE = w3.keccak(text="Sync(uint112,uint112)").hex()

async def get_uniswap_reserves(pair_address):
    try:
        async with websockets.connect(QuickNode_wss) as websocket:
            print("Successful connected to QuickNode Websocket")

            # WebSocket `logs` subscription to Uniswap Pair contract
        subscription_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_subscribe",
            "params": [
                "logs",
                {
                    "address": UNISWAP_PAIR_ETH_USDC,  # Track ETH/USDC pair contract
                    "topics": [SYNC_EVENT_SIGNATURE]  # Listen for `Sync` events only
                }
            ]
        }

        await websocket.send(json.dumps(subscription_request))
        print("Subscribed to new events!")

        while True:
            start_time = time.time()
            response = await websocket.recv()
            data = json.loads(response)

            # Extract and decode reserves from Sync event
            if "params" in data and "result" in data["params"]:
                log_data = data["params"]["result"]
                reserve_0 = int(log_data["data"][2:66], 16)  # Token0 (ETH reserve)
                reserve_1 = int(log_data["data"][66:], 16)   # Token1 (USDC reserve)

                # Convert to proper decimal format
                reserve_0_eth = reserve_0 / 10**18  # ETH (18 decimals)
                reserve_1_usdc = reserve_1 / 10**6  # USDC (6 decimals)

                end_time = time.time()

                print("ETH/USDC Reserves:")
                print(f"ETH: {reserve_0_eth} ETH")
                print(f"USDC: {reserve_1_usdc} USDC")
                print(f"Time taken to receive message: {end_time - start_time}")
                print()

    
    except Exception as e:
        print("Connection error", e)