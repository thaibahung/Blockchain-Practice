from web3 import Web3
import asyncio
import websockets
import json
import time
import math
from typing import Dict, Any, Tuple
import requests


Infura_wss = 'wss://mainnet.infura.io/ws/v3/67d4fda1bfc248aaba4b1ac954169e08'
subgraph_url = "https://gateway.thegraph.com/api/53b8386571487df55de93e545a902af7/subgraphs/id/A3Np3RQbaBA6oKJgiwDJeo5T3zrYfGHPWFYayMwtNDum"
INFURA_HTTP = "https://mainnet.infura.io/v3/67d4fda1bfc248aaba4b1ac954169e08"

# Uniswap V2 Router & Factorty Address
UNISWAP_V2_ROUTER = Web3.to_checksum_address("0x7a250d5630b4cf539739df2c5dacb4c659f2488d")
UNISWAP_V2_FACTORY_ADDRESS = Web3.to_checksum_address('0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f')

abi_types = ['uint256', 'uint256', 'address[]', 'address', 'uint256']

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

# Dictionary to store pool data: {pool_address: {token0, token1, reserve0, reserve1}}
pool_data: Dict[str, Dict[str, Any]] = {}
pair_address: Dict[Tuple[str, str], str] = {}
token_address: Dict[str, str] = {}

# Get the token address from the token symbol
def get_token_address(token_symbol):
    return token_address.get(token_symbol, None)

# Get the pair address from the token addresses
def get_pair_address(id0, id1):
    if (id0, id1) in pair_address:
        return pair_address[(id0, id1)], 0
    elif (id1, id0) in pair_address:
        return pair_address[(id1, id0)], 1
    else:
        return None, -1

# Calculate new price slippage
def calculate_price(reserve0, reserve1, token0, token1, f=0.003):
    k = reserve1 * reserve0
    if token0 > 0:
        token0 = token0 * (1 - f)
        return (reserve0 + token0) * (reserve0 + token0) / k  
    else:
        token1 = token1 * (1 - f)
        return (reserve1 + token1) * (reserve1 + token1) / k


def calculate_slippage(reserve0, reserve1, token0, token1, f=0.003):
    k = reserve1 * reserve0
    if token0 > 0:
        token0 = token0 * (1 - f)
        return k / (reserve0 + token0)
    else:
        token1 = token1 * (1 - f)
        return k / (reserve1 + token1)


def calculate_out(amount_in, id_token0, id_token1):
    pair_address, index = get_pair_address(id_token0, id_token1)
    if pair_address is None:
        return 0, 0
    if index == 1:
        id_token0, id_token1 = id_token1, id_token0
    reserve0 = pool_data[pair_address]['reserve0']
    reserve1 = pool_data[pair_address]['reserve1']

    return calculate_slippage(reserve0, reserve1, amount_in, 0), calculate_price(reserve0, reserve1, amount_in, 0)

def check_arbitrage_opportunity(edge, expected_amount):
    for st in range(len(edge)):
    return False

# Find the best arbitrage cycle
async def find_best_arbitrage_cycle(path=[], amount_in=0):
    '''
    - Tinh luong tien di vao moi diem trong path bang slippage (Tru diem cuoi cung)
    - Tinh thay doi reserve o moi diem
    - Tao do thi voi gia
    - For de kiem tra tich co lon hon 1 khong.
    '''
    for address in token_address.values():
        print(address)

    expected_amount = [-1, amount_in]
    for i in range(0, len(path)-1):
        token0 = path[i]
        token1 = path[i+1]
        expected_amount.append(calculate_out(expected_amount[-1], token0, token1)[0])
    expected_amount.append(-1)

    for i in range(0, len(path)-1):
        for j in range(i+1, len(path)):
            edge = []
            for k in range(i, j):
                token0 = path[k]
                token1 = path[k+1]
                edge.append((token0, token1))
    
            for address in token_address.values():
                edge.insert(0,(address, path[i]))
                edge.append((path[j], address))


    return
    

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

            if "params" not in data or "result" not in data["params"]:
                    continue
            
            block_number = int(data['params']['result']['number'], 16)
            full_tx = web3.eth.get_block(block_number, full_transactions=True)

            print(f"New block detected: {block_number}")

            for tx in full_tx.transactions:
                if tx['to'] != None and tx['to'].lower() == "0x7a250d5630b4cf539739df2c5dacb4c659f2488d":
                    
                    # print(tx.input[:4].lower(), tx.hash.hex())

                    if True:
                        try:
                            decoded_input = router_contract.decode_function_input(tx.input)
                            path = decoded_input[1]['path']  # The token path (array of token addresses)
                            # print(f"Path: {path}, {tx.hash.hex()}")

                            for i in range(0, len(path)-1):
                                token0 = path[i]
                                token1 = path[i+1]
                                pair_address = factory_contract.functions.getPair(token0, token1).call()
                                
                                if pair_address == '0x0000000000000000000000000000000000000000':
                                    print("Ko co pair")
                                    continue
                                
                                pair_contract = web3.eth.contract(address=pair_address, abi=PAIR_ABI)
                                reserve0, reserve1, _ = pair_contract.functions.getReserves().call()
                                
                                # print(f"Reserve0: {reserve0}, Reserve1: {reserve1}")
                                # print(f"Pair Address: {pair_address}, Token0: {token0}, Token1: {token1}, Reserve0: {reserve0}, Reserve1: {reserve1}")

                                # Store data in dictionary
                                pair_address_lower = pair_address.lower()
                                pool_data[pair_address_lower] = {
                                    'token0': token0,
                                    'token1': token1,
                                    'reserve0': reserve0,
                                    'reserve1': reserve1
                                }

                        except Exception as e:
                            print(f"Error decoding input: {e}")

            await find_best_arbitrage_cycle()

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
        
        for pair in pairs[:200]:  
            token0 = pair["token0"]["symbol"]
            token1 = pair["token1"]["symbol"]
            reserve0 = pair["reserve0"]
            reserve1 = pair["reserve1"]
            add = pair["id"]

            # Store the pair address in the dictionary
            pair_address[(pair["token0"]["id"], pair["token1"]["id"])] = add.lower()
            token_address[token0] = pair["token0"]["id"]
            token_address[token1] = pair["token1"]["id"]

            # Store data in dictionary
            pool_data[add.lower()] = {
                'token0': token0,
                'token1': token1,
                'reserve0': reserve0,
                'reserve1': reserve1
            }

async def main():
    await fetch_initial_data()
    print(f"Initial pool data loaded: {len(pool_data)} pairs")
    await listen_for_transactions()

if __name__ == "__main__":
    asyncio.run(main())

# Function to get the current pool data dictionary
def get_pool_data() -> Dict[str, Dict[str, Any]]:
    return pool_data