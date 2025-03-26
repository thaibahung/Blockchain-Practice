from web3 import Web3


web3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/67d4fda1bfc248aaba4b1ac954169e08'))


UNISWAP_V2_FACTORY_ADDRESS = Web3.to_checksum_address('0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f')  # Uniswap V2 Factory Contract address
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


tokenA = Web3.to_checksum_address('0xA0b86991C6218b36c1d19D4A2e9eb0Ce3606eB48') 
tokenB = Web3.to_checksum_address('0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2')  


factory_contract = web3.eth.contract(address=UNISWAP_V2_FACTORY_ADDRESS, abi=FACTORY_ABI)
pair_address = factory_contract.functions.getPair(tokenA, tokenB).call()
print(pair_address)

