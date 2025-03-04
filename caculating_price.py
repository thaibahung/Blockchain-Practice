import asyncio
import websockets
import json
import time
from web3 import Web3

# WebSocket connection
INFURA_WSS = "wss://mainnet.infura.io/ws/v3/67d4fda1bfc248aaba4b1ac954169e08"
w3 = Web3(Web3.LegacyWebSocketProvider(INFURA_WSS))

# Check if Web3 is Connected
if w3.is_connected():
    print("Connected to Ethereum via Infura WebSocket")
else:
    print("Connection failed")
    exit()

# Uniswap V2 Factory and Router Addresses
UNISWAP_V2_FACTORY = w3.to_checksum_address("0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f")
UNISWAP_V2_ROUTER = w3.to_checksum_address("0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D")

# Token addresses
USDT = w3.to_checksum_address("0xdAC17F958D2ee523a2206206994597C13D831ec7")
USDC = w3.to_checksum_address("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eb48")
ETH = w3.to_checksum_address("0xC02aaa39b223FE8D0A0e5C4F27eAD9083C756Cc2")  # Wrapped ETH (WETH)

# Uniswap V2 ABIs
FACTORY_ABI = json.loads('[{"constant":true,"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"}],"name":"getPair","outputs":[{"internalType":"address","name":"pair","type":"address"}],"payable":false,"stateMutability":"view","type":"function"}]')

PAIR_ABI = json.loads('[{"constant":true,"inputs":[],"name":"getReserves","outputs":[{"internalType":"uint112","name":"_reserve0","type":"uint112"},{"internalType":"uint112","name":"_reserve1","type":"uint112"},{"internalType":"uint32","name":"_blockTimestampLast","type":"uint32"}],"payable":false,"stateMutability":"view","type":"function"}]')


# Initialize Factory Contract
uniswap_factory = w3.eth.contract(address=UNISWAP_V2_FACTORY, abi=FACTORY_ABI)


def get_reserves(tokenA, tokenB):
    """Fetch reserves of a Uniswap V2 pair contract"""
    try:
        pair_address = uniswap_factory.functions.getPair(tokenA, tokenB).call()
        
        if pair_address == "0x0000000000000000000000000000000000000000":
            print(f"No pair found for {tokenA} and {tokenB}")
            return None, None
        
        pair_contract = w3.eth.contract(address=pair_address, abi=PAIR_ABI)
        reserves = pair_contract.functions.getReserves().call()
        return reserves[0], reserves[1]
    
    except Exception as e:
        print(f"Error fetching reserves for {tokenA} and {tokenB}: {e}")
        return None, None


async def subscribe():
    try:
        async with websockets.connect(INFURA_WSS) as websocket:
            print("Successfully connected to Infura WebSocket")
        
            while True:
                try:
                    # Fetch reserves for key Uniswap pools
                    print("Fetching Uniswap V2 reserves...\n")

                    start_time = time.time()
                    usdt_usdc_reserves = get_reserves(USDT, USDC)
                    usdc_eth_reserves = get_reserves(USDC, ETH)
                    eth_usdt_reserves = get_reserves(ETH, USDT)
                    end_time = time.time()

                    print(f"Time taken to fetch reserves: {end_time - start_time:.2f} seconds\n")
                    print(f"USDT/USDC Reserves: {usdt_usdc_reserves}")
                    print(f"USDC/ETH Reserves: {usdc_eth_reserves}")
                    print(f"ETH/USDT Reserves: {eth_usdt_reserves}\n")

                except Exception as msg_error:
                    print(f"Error in message processing: {msg_error}")

    except Exception as e:
        print("Connection error:", e)

asyncio.run(subscribe())
