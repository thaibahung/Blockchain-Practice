from web3 import Web3

# Connect to Ethereum node (Infura example)
w3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/67d4fda1bfc248aaba4b1ac954169e08'))

pair_address = Web3.to_checksum_address('0x03B59Bd1c8B9F6C265bA0c3421923B93f15036Fa')
# '0xee56f191001f1Ef885f67E86413f86A39976c20b'
# '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2_0xee56f191001f1ef885f67e86413f86a39976c20b_0_uniswap_v2'
# '0x66a0f676479cee1d7373f3dc2e2952778bff5bd6_0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2_0_uniswap_v2'
# 15349390856504160721159

# Minimal ABI for getReserves function only
pair_abi = [{
    "constant": True,
    "inputs": [],
    "name": "getReserves",
    "outputs": [
        {"internalType": "uint112", "name": "reserve0", "type": "uint112"},
        {"internalType": "uint112", "name": "reserve1", "type": "uint112"},
        {"internalType": "uint32", "name": "blockTimestampLast", "type": "uint32"}
    ],
    "payable": False,
    "stateMutability": "view",
    "type": "function"
}]

pair_contract = w3.eth.contract(address=pair_address, abi=pair_abi)

block_number = 22972900

  # your target block number

# Call getReserves at specific block number
reserve0, reserve1, blockTimestampLast = pair_contract.functions.getReserves().call(block_identifier=block_number)

print(f"Reserve0: {reserve0}")
print(f"Reserve1: {reserve1}")
print(f"BlockTimestampLast: {blockTimestampLast}")