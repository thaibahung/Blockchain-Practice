import asyncio
import json
import websockets
import base64
from hexbytes import HexBytes

'''
Need to install arbitrum_sdk library to run this script.
'''

# ---- Arbitrum SDK ----
# pip install arbitrum_sdk
from arbitrum_sdk.message.PubSub import ParseL2Transactions


FEED_URL = "wss://arb-seq-feed.arbitrum.io/feed"   # <-- replace with your feed URL


def decode_l2_msg(l2msg_base64: str):
    """
    Decode a single l2Msg (base64-encoded Nitro RLP blob)
    using ParseL2Transactions from the Arbitrum SDK.
    """
    try:
        # Convert base64 to raw bytes
        raw_bytes = base64.b64decode(l2msg_base64)

        # Parse L2 transactions (Arbitrum Nitro format)
        txs = ParseL2Transactions(raw_bytes)

        decoded = []
        for tx in txs:
            decoded.append({
                "from": tx.sender,
                "to": tx.to,
                "nonce": tx.nonce,
                "value": tx.value,
                "gas": tx.gas,
                "gasPrice": tx.gasPrice,
                "data": tx.data.hex(),
                "chainId": tx.chainId,
            })

        return decoded

    except Exception as e:
        return {"error": str(e)}


async def read_message(msg):
    """
    Process each message from Sequencer Feed
    """
    try:
        # The real payload is nested here:
        content = msg[0]["message"]["message"]
        
        l2msg = content["l2Msg"]

        decoded = decode_l2_msg(l2msg)

        print("\n========== NEW L2 MESSAGE ==========")
        print(json.dumps(decoded, indent=2))

    except Exception as e:
        print("[ERROR] Failed to parse message:", e)
        print("Raw:", msg)


async def listen_to_feed():
    print(f"Connecting to {FEED_URL}...")
    async with websockets.connect(FEED_URL) as ws:
        print("Connected. Listening...\n")

        while True:
            try:
                raw = await ws.recv()
                msg = json.loads(raw)

                # messages come as lists
                await read_message(msg)

            except Exception as e:
                print("[ERROR] Listening error:", e)
                await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(listen_to_feed())
