import asyncio
import websockets
import json

ETH_WS_URL = 'wss://mainnet.infura.io/ws/v3/67d4fda1bfc248aaba4b1ac954169e08'

async def subscribe():
    try:
        async with websockets.connect(ETH_WS_URL) as websocket:
            print("Successful connected to Ethereum Websocket")

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

            # Send a sub request for pending tx in the mempool.=
            subscription_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "eth_subscribe",
                "params": ["newPendingTransactions"]
            }

            await websocket.send(json.dumps(subscription_request))
            print("Subscribed to new information!")

            while True:
                response = await websocket.recv()
                data = json.loads(response)
                print("New Message:", data)
                print()

    except Exception as e:
        print("Connection error", e)

asyncio.run(subscribe())