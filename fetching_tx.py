import asyncio
import websockets
import json
import time
import requests

Infura_wss = 'wss://mainnet.infura.io/ws/v3/67d4fda1bfc248aaba4b1ac954169e08'
Infura_http = "https://mainnet.infura.io/v3/67d4fda1bfc248aaba4b1ac954169e08"
QuickNode_wss = "wss://wiser-dark-theorem.quiknode.pro/6616c8f18079c8fc568bab2c163a6dba439d5c9f"

# Uniswap V2 Router Address
UNISWAP_V2_ROUTER = "0x7a250d5630b4cf539739df2c5dacb4c659f2488d"

# Uniswap V2 Function Signatures (First 4 bytes of calldata)
UNISWAP_V2_FUNCTIONS = {
    "swapExactETHForTokens": "0x7ff36ab5",
    "swapExactTokensForETH": "0x18cbafe5",
    "swapExactTokensForTokens": "0x38ed1739",
    "swapETHForExactTokens": "0xfb3bdb41" 
}

async def fetch_transaction_details(tx_hash):
    # Fetch transaction details (values, from add, to add) from Ethereum.
    fetch_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_getTransactionByHash",
        "params": [tx_hash]
    }

    response = requests.post(Infura_http, json=fetch_request)
    return response.json().get("result")


async def process_transaction(tx_hash):
    # Check if a transaction is related to Uniswap V2 AMM.
    tx_details = await fetch_transaction_details(tx_hash)

    if not tx_details or "to" not in tx_details or "input" not in tx_details:
        return

    to_address = tx_details["to"]
    input_data = tx_details["input"]

    # Check if transaction is sent to Uniswap V2 Router
    if to_address and to_address.lower() == UNISWAP_V2_ROUTER.lower():
        function_signature = input_data[:10]  # First 4 bytes of calldata (10 characters including '0x')

        # Check if function signature matches Uniswap V2 swap functions
        if function_signature in UNISWAP_V2_FUNCTIONS.values():
            print("**Uniswap V2 Swap Transaction Detected!**")
            print(f"TX Hash: {tx_hash}")
            print(f"Interacting Contract: {to_address} (Uniswap V2 Router)")
            # print(f"Function: {list(UNISWAP_V2_FUNCTIONS.keys())[list(UNISWAP_V2_FUNCTIONS.values()).index(function_signature)]}")
            print(f"Input Data: {input_data[:50]}...\n")


async def subscribe():
    try:
        async with websockets.connect(QuickNode_wss) as websocket:
            print("Successful connected to QuickNode Websocket")

            '''
            - jsonrpc -> Defines the JSON-RPC protocol version -> (= 2.0) Ensures compatibility with Ethereum JSON-RPC nodes
            - id -> A unique identifier for the request -> Used to match the response with the request
            - method -> Specifies the Ether JSON-RPC function -> "eth_subscribe" tells Ether to create a Websocket subscription
            - params -> holds the arguments for "method" 
            '''

            # Send a sub request for pending tx in the mempool.
            subscription_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "eth_subscribe",
                "params": ["newPendingTransactions"]
            }

            await websocket.send(json.dumps(subscription_request))
            print("Subscribed to new information!")

            while True:
                start_time = time.time() # Record time before waiting for response
                response = await websocket.recv()

                data = json.loads(response)
                if "params" not in data or "result" not in data["params"]:
                    continue

                tx_hash = data["params"]["result"]
                await process_transaction(tx_hash)

                end_time = time.time()
                print("Time taken to receive message:", end_time - start_time)
                print()

    except Exception as e:
        print("Connection error", e)

asyncio.run(subscribe())