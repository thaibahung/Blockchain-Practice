from web3 import Web3

# Connect to an Ethereum node (Infura or local node)
INFURA_URL = "https://mainnet.infura.io/v3/67d4fda1bfc248aaba4b1ac954169e08"
web3 = Web3(Web3.HTTPProvider(INFURA_URL))

# Uniswap V2 Router contract address (Mainnet)
UNISWAP_V2_ROUTER = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"  

# Uniswap V2 Router ABI (only including getAmountsOut function)
UNISWAP_V2_ROUTER_ABI = [
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"}
        ],
        "name": "getAmountsOut",
        "outputs": [
            {"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

# Initialize Uniswap Router Contract
uniswap_router = web3.eth.contract(address=UNISWAP_V2_ROUTER, abi=UNISWAP_V2_ROUTER_ABI)

def get_swap_amount(amount_in, token_in, token_out):
    """
    Get the estimated output amount for swapping token_in to token_out.
    
    :param amount_in: Amount of input token (in smallest units, e.g., wei for ETH)
    :param token_in: Address of input token
    :param token_out: Address of output token
    :return: Estimated output amount
    """
    path = [token_in, token_out]  # Swap path (direct swap)
    
    try:
        amounts = uniswap_router.functions.getAmountsOut(amount_in, path).call()
        return amounts[1]  # The estimated output amount
    except Exception as e:
        print(f"Error fetching swap amount: {e}")
        return None

# Example Usage
TOKEN_IN = "0xC02aaa39b223FE8D0A0e5C4F27eAD9083C756Cc2"  # WETH
TOKEN_OUT = "0x6b175474e89094c44da98b954eedeac495271d0f"  # DAI
AMOUNT_IN_WEI = web3.to_wei(3261217484088194341, 'ether')  # 1 WETH in Wei

estimated_amount_out = get_swap_amount(AMOUNT_N_WEI, TOKEN_IN, TOKEN_OUT)

if estimated_amount_out:
    print(f"Estimated Output: {web3.from_wei(estimated_amount_out, 'ether')} USDT")