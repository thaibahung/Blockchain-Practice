from web3 import Web3
import os

# 1. Connect to an Ethereum node (e.g., Infura)
infura_url = os.getenv("WEB3_PROVIDER_URI", "https://mainnet.infura.io/v3/67d4fda1bfc248aaba4b1ac954169e08")
w3 = Web3(Web3.HTTPProvider(infura_url))

# 2. Specify your Uniswap V2 pair address
pair_address = Web3.to_checksum_address("0xdAB143548832194C8F2677eba9830E0B453B37C6")

# 3. Minimal ABI for getReserves()
pair_abi = [
    {
        "constant": True,
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"internalType": "uint112", "name": "_reserve0", "type": "uint112"},
            {"internalType": "uint112", "name": "_reserve1", "type": "uint112"},
            {"internalType": "uint32",  "name": "_blockTimestampLast", "type": "uint32"},
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
    }
]

# 4. Instantiate the contract
pair_contract = w3.eth.contract(address=pair_address, abi=pair_abi)

# 5. Call getReserves()
reserve0, reserve1, block_timestamp_last = pair_contract.functions.getReserves().call()

print(f"Reserve0 (token0): {reserve0}")
print(f"Reserve1 (token1): {reserve1}")
print(f"Last Update Timestamp: {block_timestamp_last}")

