import asyncio
from web3 import Web3
import json
import os
from logger import logger

from config import (
    THEGRAPH_API_KEY, INFURA_API_KEY, UNISWAP_V2_THEGRAPH, Optimistic_MEV_ABI, 
    PRIVATE_KEY, ACCOUNT_ADDRESS
)

from infrastructure.data_providers.graph.edge import Edge
from infrastructure.data_providers.graph.cycle import Cycle_3, Cycle_2

async def main():
    w3 = Web3(Web3.HTTPProvider(f"https://sepolia.infura.io/v3/{INFURA_API_KEY}"))
    print("Connected:", w3.is_connected())
    print("Chain ID:", w3.eth.chain_id)

    arb_checker = w3.eth.contract(
        address=Web3.to_checksum_address("0xEfb756900943B23401564e199a4e95BE650CD499"),
        abi = json.loads(Optimistic_MEV_ABI)
    )

    # Example pool addresses
    POOL_WEPA_WETH_V2 = Web3.to_checksum_address("0xf5CacD62814d8fB949c71fDB4a66A620Bc88aD8D")
    POOL_WEPA_BORI_V2 = Web3.to_checksum_address("0x0Fb1274e69556874029C1050eCF4e2035BC0e8D0")
    POOL_BORI_WETH_V2 = Web3.to_checksum_address("0x910814636DC66634dA77dc271defae434FFec431")

    # Example token addresses
    WEPA = Web3.to_checksum_address("0x1817537bca9300c65ED8a8e68A25974F04D36C1F")  # 6 decimals
    WETH = Web3.to_checksum_address("0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14")  # Wrapped ETH (ERC20)
    BORI = Web3.to_checksum_address("0x82AF6695E273A1D5Ffc57b4F49D2f61f20B0aA64")  # Uniswap token

    # Example Edge
    edge1 = (POOL_WEPA_WETH_V2, 30, 0)
    edge2 = (POOL_BORI_WETH_V2, 30, 0)
    edge3 = (POOL_WEPA_BORI_V2, 30, 0)

    cycle = (
        WEPA,
        WETH,
        BORI,
        edge1,
        edge2,
        edge3
    )

    cycles = [cycle]

    amount_in = 1000000000  # 1 USDC with 6 decimals

    profits = arb_checker.functions.checkProfit(amount_in, cycle).call()
    print(profits)

    
    nonce = w3.eth.get_transaction_count(ACCOUNT_ADDRESS)
    gas_price = w3.eth.gas_price

    tx = arb_checker.functions.checkProfit(amount_in, cycle).build_transaction({
        "from": ACCOUNT_ADDRESS,
        "gas": 1000000,
        "gasPrice": gas_price,
        "nonce": nonce,
        "chainId": w3.eth.chain_id,
    })

    # Sign locally
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)

    # Send to Infura
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print("Transaction sent:", tx_hash.hex())

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print("Transaction confirmed in block", receipt.blockNumber)

    event_signature_hash = w3.keccak(text="Debug(string,uint256)").hex()
    event_signature_hash_2 = w3.keccak(text="DebugPool(string,Edge)").hex()

    for log in receipt.logs:
        if log['topics'][0].hex() == event_signature_hash:
            decoded = arb_checker.events.Debug().process_log(log)
            print("Debug:", decoded['args'])
        elif log['topics'][0].hex() == event_signature_hash_2:
            decoded = arb_checker.events.DebugPool().process_log(log)
            print("DebugPool:", decoded['args'])

if __name__ == "__main__":
    asyncio.run(main())


