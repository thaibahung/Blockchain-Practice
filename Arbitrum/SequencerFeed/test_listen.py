import asyncio
import websockets
import json
import base64
from web3 import Web3
from eth_utils import function_signature_to_4byte_selector
from datetime import datetime
from logger import logger
import sys, pathlib
from eth_account import Account

# --- CONFIGURATION ---
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from config import INFURA_API_KEY, UNISWAP_V2_ROUTER, UNISWAP_V2_ROUTER_ABI

FEED_URL = "wss://arb1-feed.arbitrum.io/feed"

w3 = Web3(Web3.HTTPProvider(f"https://arbitrum-mainnet.infura.io/v3/{INFURA_API_KEY}"))
logger.info(f"Connected: {w3.is_connected()}")

router_contract = w3.eth.contract(address=UNISWAP_V2_ROUTER, abi=UNISWAP_V2_ROUTER_ABI)

L1MessageType_L2Message = 3
L2MessageKind_SignedTx = 4

async def decode_l2_message(encoded_msg_b64: str):
    """Decodes the Base64 l2Msg field into a dict transaction."""
    try:
        raw_bytes = base64.b64decode(encoded_msg_b64)
    except Exception:
        return None

    # -- First byte = L2 message kind
    msg_kind = raw_bytes[0]
    if msg_kind != L2MessageKind_SignedTx:
        return None

    # Remove first byte to expose raw RLP/typed tx
    tx_raw = raw_bytes[1:]

    # print(tx_raw)

    try:
        tx = Account.decode_transaction(tx_raw)
        print(tx)
        # Compute L2 hash (simple keccak for now)
        tx_hash = w3.keccak(tx_raw).hex()
        tx["hash"] = tx_hash

        return tx

    except Exception as e:
        print("Transaction decode error:", e)
        return None


async def read_mess(message):
    """Extracts l2Msg and decodes the embedded signed transaction."""
    parsed = json.loads(message)
    messages = parsed.get("messages")
    if not messages:
        return

    l2Msg = messages[0]["message"]["message"]["l2Msg"]
    data = base64.b64decode(l2Msg).hex()
    print(data)
    return

    tx = await decode_l2_message(l2Msg)
    if not tx:
        return

    router = tx.get("to")
    data = tx.get("data")

    print(f"\n--- NEW L2 TX ---")
    print("Hash:", tx["hash"])
    print("To (router):", router)
    print("Data length:", len(data) if data else 0)

    return


async def listen_to_feed():
    """Connects to Arbitrum sequencer feed."""
    print(f"Connecting to {FEED_URL}...")
    try:
        async with websockets.connect(FEED_URL) as websocket:
            print("Connected. Listening...")
            while True:
                message = await websocket.recv()
                asyncio.create_task(read_mess(message))

    except websockets.exceptions.ConnectionClosedOK:
        print("Connection closed gracefully.")
    except Exception as e:
        print("Feed error:", e)


# --- RUN ---
if __name__ == "__main__":
    try:
        asyncio.run(listen_to_feed())
    except KeyboardInterrupt:
        print("Stopped by user.")
