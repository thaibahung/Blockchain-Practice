import asyncio
import websockets
import time
import requests

Infura_wss = 'wss://mainnet.infura.io/ws/v3/67d4fda1bfc248aaba4b1ac954169e08'
subgraph_url = "https://gateway.thegraph.com/api/53b8386571487df55de93e545a902af7/subgraphs/id/A3Np3RQbaBA6oKJgiwDJeo5T3zrYfGHPWFYayMwtNDum"
with open("query.graphql","r") as file:
    st = file.read().strip()

query = {"query": st}
response = requests.post(subgraph_url, json=query)

if response.status_code == 200:
    print("Oke")
    data = response.json()
    pairs = data["data"]["pairs"]

    for pair in pairs[:10]:  
        token0 = pair["token0"]["symbol"]
        token1 = pair["token1"]["symbol"]
        reserve0 = pair["reserve0"]
        reserve1 = pair["reserve1"]

        block_number = (
            pair["swaps"][0]["transaction"]["blockNumber"]
            if pair["swaps"]
            else "N/A"
        )
        print(f"{token0}/{token1} - Reserve0: {reserve0} - Reserve1: {reserve1}, Block: {block_number}")
else:
    print("Kiểm Tra Lại", response.status_code, response.text)