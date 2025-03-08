from web3 import Web3

INFURA_URL = "https://mainnet.infura.io/v3/67d4fda1bfc248aaba4b1ac954169e08"
web3 = Web3(Web3.HTTPProvider(INFURA_URL))

if web3.is_connected():
    print("Oke")
else:
    print("Connection failed")

with open("swaptx.graphql","r") as file:
    UNISWAP_V2_PAIR_ABI  = file.read().strip()

# print(type(UNISWAP_V2_PAIR_ABI))

def get_swap_details(tx_hash, pair_address):
    pair_contract = web3.eth.contract(address=pair_address, abi=UNISWAP_V2_PAIR_ABI)

    # Get reserves before the swap
    reserves_before = pair_contract.functions.getReserves().call()
    reserve0_before, reserve1_before = reserves_before[0], reserves_before[1]


    tx_receipt = web3.eth.get_transaction_receipt(tx_hash)
    
    # Extract swap event
    swap_event = None
    for log in tx_receipt['logs']:
        if log['address'].lower() == pair_address.lower():
            try:
                decoded_event = pair_contract.events.Swap().process_log(log)
                swap_event = decoded_event['args']
                break
            except:
                continue

    if not swap_event:
        print("No swap event found in transaction.")
        return None

    # Extract swap details
    amount0_in = swap_event['amount0In']
    amount1_in = swap_event['amount1In']
    amount0_out = swap_event['amount0Out']
    amount1_out = swap_event['amount1Out']

    # Determine token in and token out
    if amount0_in > 0:
        token_in = "token0"
        token_out = "token1"
    else:
        token_in = "token1"
        token_out = "token0"

    
    print("reserve0_before", reserve0_before)
    print("reserve1_before", reserve1_before)
    print("amount0_in", amount0_in)
    print("amount1_in", amount1_in)
    print("amount0_out", amount0_out)
    print("amount1_out", amount1_out)
    print("token_in", token_in)
    print("token_out", token_out)

PAIR_ADDRESS = Web3.to_checksum_address("0xa478c2975ab1ea89e8196811f51a7b7ade33eb11")  # WETH/DAI Pair
TX_HASH = "0xe099193ea483d008959639c21a8c876a8e1b5da543dfaa21be6c5979a679daa3"

get_swap_details(TX_HASH, PAIR_ADDRESS)
