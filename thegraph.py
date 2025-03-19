import asyncio
import websockets
import time
import requests
import csv
import json

Infura_wss = 'wss://mainnet.infura.io/ws/v3/67d4fda1bfc248aaba4b1ac954169e08'
subgraph_url = "https://gateway.thegraph.com/api/53b8386571487df55de93e545a902af7/subgraphs/id/A3Np3RQbaBA6oKJgiwDJeo5T3zrYfGHPWFYayMwtNDum"

# Uniswap V2 Router Address (lowercase)
UNISWAP_V2_ROUTER = "0x7a250d5630b4cf539739df2c5dacb4c659f2488d"


with open("query.graphql","r") as file:
    st = file.read().strip()

with open("request.csv", "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["Token Pair", "Reserve0", "Reserve1", "Last Block Updated"])

with open("mempool_tx.csv", "w", newline= "") as file:
    write = csv.writer(file)
    write.writerow(["Liquid Pool Hash", "Gas Price", "Value", "Transaction Hash"])


async def listen_for_new_blocks():
    try:
        async with websockets.connect(Infura_wss) as websocket:
            print("Infura wss Oke")

            # Get the latest block number from the WebSocket
            subscription_request = {
                "jsonrpc": "2.0",
                "method": "eth_subscribe",
                "params": ["newHeads"],
                "id": 1
            }

            await websocket.send(json.dumps(subscription_request))
            
            while True:
                start_time = time.time()
                response = await websocket.recv()
                data = json.loads(response)
                # new_block = int(data["params"]["result"]["number"], 16)
                
                # Query tu thegraph
                await fetch_lastest_data()

                end_time = time.time()
                if "params" in data and "result" in data["params"]:
                    new_block = int(data["params"]["result"]["number"], 16)
                    print(f"New block detected: {new_block}")
                print("Time taken to receive message:", end_time - start_time)

    except Exception as e:
        print("Lỗi rồi cu", e)



async def fetch_lastest_data():
    query = {"query": st}
    response = requests.post(subgraph_url, json=query)

    if response.status_code == 200:
        print("Oke")
        data = response.json()
        pairs = data["data"]["pairs"]

        block_number = data["data"]["_meta"]["block"]["number"]
        # print(block_number)
        with open('request.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([block_number])

        for pair in pairs[:10]:  
            token0 = pair["token0"]["symbol"]
            token1 = pair["token1"]["symbol"]
            reserve0 = pair["reserve0"]
            reserve1 = pair["reserve1"]

            block_number = '0'
            block_number = max(block_number, (
                pair["swaps"][0]["transaction"]["blockNumber"]
                if pair["swaps"]
                else "N/A"
            ))

            block_number = max(block_number, (
                pair["mints"][0]["transaction"]["blockNumber"]
                if pair["mints"]
                else "N/A"
            ))

            block_number = max(block_number, (
                pair["burns"][0]["transaction"]["blockNumber"]
                if pair["burns"]
                else "N/A"
            ))

            #print(block_number)

            with open('request.csv', 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([f"{token0}/{token1}", reserve0, reserve1, block_number])
            # print(f"{token0}/{token1} - Reserve0: {reserve0} - Reserve1: {reserve1}, Block: {block_number}")

    else:
        print("Kiểm Tra Lại", response.status_code, response.text)




async def main():
    await listen_for_new_blocks()


if __name__ == "__main__":
    asyncio.run(main())
    

'''
- Dùng websocket để lấy blocknumber eth gần nhất (cũng như để check coi thegraph bị chậm ko)
- Khi wss có kết quả thì query từ the graph.
'''