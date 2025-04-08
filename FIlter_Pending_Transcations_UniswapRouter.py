import asyncio
import json
from web3 import Web3
from websockets import connect

ALCHEMY_WS = "wss://eth-mainnet.g.alchemy.com/v2/9qCuMumrhLZzVLIRFV9mELoZ-TlKOFzU"
ALCHEMY_RPC = "https://eth-mainnet.g.alchemy.com/v2/9qCuMumrhLZzVLIRFV9mELoZ-TlKOFzU"
INFURA_WS = "wss://mainnet.infura.io/ws/v3/e6d19ba5f542418ba8acef84ed1427a8"
INFURA_HTTP = "https://mainnet.infura.io/v3/e6d19ba5f542418ba8acef84ed1427a8"
QUICKNODE_RPC = "https://yolo-aged-darkness.quiknode.pro/401a21cac95f67e72bb1478cf94b4ff0763535cc/"
QUICKNODE_WSS = "wss://yolo-aged-darkness.quiknode.pro/401a21cac95f67e72bb1478cf94b4ff0763535cc"
SUSHISWAP_ROUTER = "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F"
PANCAKESWAPV2_ROUTER = "0xEfF92A263d31888d860bD50809A8D171709b7b1c"
UNISWAPV3_ROUTER = "0xe592427a0aece92de3edee1f18e0157c05861564"
UNISWAPV2_ROUTER = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
web3 = Web3(Web3.HTTPProvider(ALCHEMY_RPC))
print(f'Connected via HTTP: {web3.is_connected()}')
#--------------------------Connection Setup stuff -------------------------------#


def EventHandler(pending_tx): 
    """Takes in a subscription transacton response as pending_tx
       Then currently prints out data or can be modified for whatever"""
    transaction = json.loads(pending_tx)
    #print(transaction)
    txHash = transaction['params']['result']
    transactionData = web3.eth.get_transaction(txHash)
    toAddress = transactionData['to']
    #print(toAddress)
    #Filter transactions to Uniswap V2 Router: 
    if str(toAddress) == str(PANCAKESWAPV2_ROUTER):
        print("found this bro " + txHash)  


#--------------------------Start Subscribe Pending TX -------------------------------#
#This code actually grabs the pending transactons from the mempool
#Reference: https://docs.alchemy.com/reference/newpendingtransactions
#           https://websockets.readthedocs.io/en/3.4/intro.html
async def subscribePendingTX():
    """Subscribes to the mempool listening for pending transactions
       Sends off the responses to be processed by the eventhandler function"""
    async with connect(ALCHEMY_WS, ping_interval = 30) as ws:
        await ws.send('{"jsonrpc": "2.0", "id": 1, "method": "eth_subscribe", "params": ["newPendingTransactions"]}')
       
        while True:
            try:
                pending_tx = await asyncio.wait_for(ws.recv(), timeout=15)
                EventHandler(pending_tx)
            except:
                pass

                

if __name__ == "__main__":
        asyncio.run(subscribePendingTX())
