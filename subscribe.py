import asyncio
import websockets
import json
import time

Infura_wss = 'wss://mainnet.infura.io/ws/v3/67d4fda1bfc248aaba4b1ac954169e08'
QuickNode_wss = "wss://wiser-dark-theorem.quiknode.pro/6616c8f18079c8fc568bab2c163a6dba439d5c9f"

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

            # Send a sub request to listen for new blocks
            '''
            subscription_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "eth_subscribe",
                "params": ["newHeads"]
            }
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
                end_time = time.time()

                data = json.loads(response)
                print("New Message:", data)
                print()
                print("Time taken to receive message:", end_time - start_time)

    except Exception as e:
        print("Connection error", e)

asyncio.run(subscribe())