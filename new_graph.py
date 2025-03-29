from web3 import Web3
import asyncio
import websockets
import json
import time
import requests
import csv


Infura_wss = 'wss://mainnet.infura.io/ws/v3/67d4fda1bfc248aaba4b1ac954169e08'
subgraph_url = "https://gateway.thegraph.com/api/53b8386571487df55de93e545a902af7/subgraphs/id/A3Np3RQbaBA6oKJgiwDJeo5T3zrYfGHPWFYayMwtNDum"
INFURA_HTTP = "https://mainnet.infura.io/v3/67d4fda1bfc248aaba4b1ac954169e08"

# Uniswap V2 Router & Factorty Address
UNISWAP_V2_ROUTER = Web3.to_checksum_address("0x7a250d5630b4cf539739df2c5dacb4c659f2488d")
UNISWAP_V2_FACTORY_ADDRESS = Web3.to_checksum_address('0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f')

abi_types = ['uint256', 'uint256', 'address[]', 'address', 'uint256']

swap_selectors = {
    b'\x38\xed\x17\x39',  # swapExactTokensForTokens selector
    b'\x88\x03\xdb\xee',  # swapExactTokensForETH selector
    b'\x4a\x25\xd9\x4a',  # swapTokensForExactTokens selector
    b'\x18\xcb\xaf\xe5',  # swapETHForExactTokens selector
    b'\x5c\x11\x5d\x9f',  # swapExactETHForTokens selector
    b'\x7f\xf3j\x6a\xb5'   # 'swapExactETHForTokens(uint256,address[],address,uint256)',
    b'\xfb\x3b\xdb\x41'   # 'swapETHForExactTokens(uint256,address[],address,uint256)',
    b'\xb6\xf9\xde\x95'   # 'swapExactTokensForTokensSupportingFeeOnTransferTokens(uint256,uint256,address[],address,uint256)',
    b'\x79\x1a\xc9\x47'   # 'swapTokensForExactTokensSupportingFeeOnTransferTokens(uint256,uint256,address[],address,uint256)',
    b'\xd0\x6c\xa0\x61'   # swapExactETHForTokensSupportingFeeOnTransferTokens(uint256,address[],address,uint256)'
}

# Cac ABI can thiet

with open("minimal_abi.json","r") as file:
    minimal_abi = json.load(file)

FACTORY_ABI = '''[
    {
        "constant": true,
        "inputs": [
            { "name": "tokenA", "type": "address" },
            { "name": "tokenB", "type": "address" }
        ],
        "name": "getPair",
        "outputs": [
            { "name": "", "type": "address" }
        ],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    }
]'''

PAIR_ABI = '''[
    {
        "constant": true,
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            { "name": "reserve0", "type": "uint112" },
            { "name": "reserve1", "type": "uint112" },
            { "name": "blockTimestampLast", "type": "uint32" }
        ],
        "payable": false,
        "stateMutability": "view",
        "type": "function"
    }
]'''

# Khoi tao web3 va cac thu can theit
web3 = Web3(Web3.HTTPProvider(INFURA_HTTP))
router_contract = web3.eth.contract(address=UNISWAP_V2_ROUTER, abi=minimal_abi) # Contract de decode
factory_contract = web3.eth.contract(address=UNISWAP_V2_FACTORY_ADDRESS, abi=FACTORY_ABI) # Contract de lay reserve

with open("request.csv", "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["Token Pair", "Reserve0", "Reserve1", "Pair Address"])

async def listen_for_transactions():
    async with websockets.connect(Infura_wss) as websocket:
        print("Ket noi wss oke")

        subscription_request = {
                "id": 1,
                "method": "eth_subscribe",
                "params": ["newHeads"]
            }
        
        queue = []
        await websocket.send(json.dumps(subscription_request))
        
        while True:
            response = await websocket.recv()
            data = json.loads(response)

            # print(data)

            if "params" not in data or "result" not in data["params"]:
                    continue
            
            block_number = int(data['params']['result']['number'], 16)
            full_tx = web3.eth.get_block(block_number, full_transactions=True)

            print(f"New block detected: {block_number}")
            for tx in full_tx.transactions:
                if tx['to'] != None and tx['to'].lower() == "0x7a250d5630b4cf539739df2c5dacb4c659f2488d":
                    
                    print(tx.input[:4].lower(), tx.hash.hex())

                    # if tx.input[:4].lower() in swap_selectors:
                    if True:
                        try:
                            decoded_input = router_contract.decode_function_input(tx.input)
                            # decoded_input_2 = web3.eth.decode
                            #print(decoded_input)
                            path = decoded_input[1]['path']  # The token path (array of token addresses)
                            print(f"Path: {path}, {tx.hash.hex()}")

                            for i in range(0, len(path)-1):
                                token0 = path[i]
                                token1 = path[i+1]
                                pair_address = factory_contract.functions.getPair(token0, token1).call()
                                
                                if pair_address == '0x0000000000000000000000000000000000000000':
                                    print("Ko co pair")
                                    continue
                                
                                pair_contract = web3.eth.contract(address=pair_address, abi=PAIR_ABI)
                                reserve0, reserve1, _ = pair_contract.functions.getReserves().call()
                                
                                print(f"Reserve0: {reserve0}, Reserve1: {reserve1}")
                                
                                # Viet vao csv
                                with open('request.csv', 'r') as file:
                                    lines = file.readlines()

                                with open("request.csv", "r+", newline="") as file:
                                    pair_address = pair_address.lower()
                                    for line in lines:
                                        if pair_address in line:
                                            updated_line = f"{token0}/{token1}, {reserve0}, {reserve1}, {pair_address}\n"
                                            file.write(updated_line)
                                            break

                        except Exception as e:
                            print(f"Error decoding input: {e}")


# Lay thong tin id pool tu dau tu the graph
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
    await listen_for_transactions()

if __name__ == "__main__":
    asyncio.run(main())

'''
Còn vài bước tối ưu:
- Sửa bước decode -> json prettier
- So sanh block number
- Tối ưu cách ghi vào file csv
- Ghi đúng thứ tự reserve0/reserve1 (nên là cái bé đúng trước)
'''