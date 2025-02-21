import asyncio
import websockets
import json

ETH_WS_URL = 'wss://mainnet.infura.io/ws/v3/67d4fda1bfc248aaba4b1ac954169e08'

async def subscribe():
    try:
        async with websockets.connect(ETH_WS_URL) as websocket:
            print("Successful connected to Ethereum Websocket")

            # Send a sub request to listen for new blocks
            subscription_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "eth_subscribe",
                "params": ["newHeads"]
            }

            await websocket.send(json.dumps(subscription_request))
            print("Subscribed to new block headers!")

            while True:
                response = await websocket.recv()
                data = json.loads(response)
                print("New Message:", data)
                print()

    except Exception as e:
        print("Connection error", e)

asyncio.run(subscribe())