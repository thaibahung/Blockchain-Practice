import web3
import asyncio
import websockets
import json
import time
import requests
import csv

Infura_wss = 'wss://mainnet.infura.io/ws/v3/67d4fda1bfc248aaba4b1ac954169e08'
subgraph_url = "https://gateway.thegraph.com/api/53b8386571487df55de93e545a902af7/subgraphs/id/A3Np3RQbaBA6oKJgiwDJeo5T3zrYfGHPWFYayMwtNDum"

with open("request.csv", "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["Token Pair", "Reserve0", "Reserve1", "Pair Address"])

async def fetch_initial_data():
    with open("initial_query.graphql","r") as file:
        st = file.read().strip()
    
    query = {"query": st}
    response = requests.post(subgraph_url, json=query)

    if response.status_code == 200:
        print("Oke")
        data = response.json()
        pairs = data["data"]["pairs"]

        # Block number gan nhat lay tu graph
        block_number = data["data"]["_meta"]["block"]["number"]

        with open('request.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([block_number])
        
        for pair in pairs[:10]:  
            token0 = pair["token0"]["symbol"]
            token1 = pair["token1"]["symbol"]
            reserve0 = pair["reserve0"]
            reserve1 = pair["reserve1"]
            add = pair["id"]

            with open('request.csv', 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([f"{token0}/{token1}", reserve0, reserve1, add])

async def main():
    await fetch_initial_data()

if __name__ == "__main__":
    asyncio.run(main())