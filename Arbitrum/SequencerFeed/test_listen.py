import asyncio
import websockets
import brotli
from eth_utils import decode_hex
from eth_account import Account
from eth_abi import decode as abi_decode
from hexbytes import HexBytes
from web3 import Web3
import json
import struct
import base64
from eth_account import Account
from eth_account.typed_transactions import TypedTransaction
from eth_account._utils.legacy_transactions import Transaction, vrs_from
from eth_account._utils.signing import hash_of_signed_transaction
import rlp
from eth_utils import to_hex

FEED_URL = "wss://arb1-feed.arbitrum.io/feed"

# Nitro message kinds
L2MessageKind_UnsignedUserTx = 0
L2MessageKind_ContractTx = 1
L2MessageKind_NonmutatingCall = 2
L2MessageKind_Batch = 3
L2MessageKind_SignedTx = 4
L2MessageKind_Heartbeat = 5
L2MessageKind_SignedCompressedTx = 6   # not yet used

def read_u8(data, offset):
    """Read a single byte as an integer."""
    return data[offset], offset + 1

def read_bytestring(data, offset):
    """
    Read a length-prefixed bytestring.
    Format: [4 bytes big-endian length] [data]
    """
    if offset + 4 > len(data):
        raise ValueError("Bytestring header out of bounds")
    
    length = struct.unpack(">I", data[offset:offset+4])[0]
    offset += 4
    
    if offset + length > len(data):
        raise ValueError("Bytestring data out of bounds")
        
    segment = data[offset:offset+length]
    offset += length
    return segment, offset

'''
def decode_signed_tx(raw_tx: bytes | str):
    """
    Decode a signed Ethereum tx (legacy or typed) into a dict.
    raw_tx can be bytes or a hex string.
    """
    txn_bytes = HexBytes(raw_tx)

    if len(txn_bytes) == 0:
        raise ValueError("Empty transaction bytes")

    first = txn_bytes[0]

    # Typed transaction per EIP-2718: prefix type byte (0x01, 0x02, 0x03, ...)
    if first <= 0x7F:
        tx = TypedTransaction.from_bytes(txn_bytes)
        msg_hash = tx.hash()
        v, r, s = tx.vrs()
    else:
        # Legacy RLP-encoded transaction
        tx = Transaction.from_bytes(txn_bytes)
        msg_hash = hash_of_signed_transaction(tx)
        v, r, s = vrs_from(tx)

    # Recover sender
    sender = Account._recover_hash(msg_hash, vrs=(v, r, s))

    data = tx.as_dict()

    # Normalise `to`
    if isinstance(data.get("to"), (bytes, bytearray)):
        to_bytes = data["to"]
        data["to"] = None if len(to_bytes) == 0 else Web3.to_checksum_address(to_bytes)

    # Normalise `data`
    if isinstance(data.get("data"), (bytes, bytearray)):
        data["data"] = "0x" + data["data"].hex()

    data["from"] = Web3.to_checksum_address(sender)

    return data
'''

def decode_L2Message(data):
    offset = 0
    kind, offset = read_u8(data, offset)
    decoded_items = []
    #print(kind, offset)

    # ───────────────────────────────────────────────
    # KIND 4 = SignedTx (normal Ethereum signed tx)
    # ───────────────────────────────────────────────
    if kind == L2MessageKind_SignedTx:
        print("  -> Type: Signed Transaction")
        tx_bytes = data[offset:] # The rest of the data is the RLP encoded tx
        try:
            # Check for Typed Transaction (EIP-2718)
            # If the first byte is in [0, 0x7f], it's a typed tx.
            # Legacy txs start with >= 0xc0 (RLP list)
            
            if len(tx_bytes) == 0:
                 decoded_items.append({"kind": "SignedTx", "error": "Empty transaction bytes"})
                 return decoded_items

            first_byte = tx_bytes[0]
            if first_byte <= 0x7f:
                print(1)
                tx_type = first_byte
                rlp_data = tx_bytes[1:]
                decoded_rlp = rlp.decode(rlp_data)
                
                # Map fields based on type
                tx_data = {}
                if tx_type == 2: # EIP-1559
                    # [chain_id, nonce, max_priority_fee_per_gas, max_fee_per_gas, gas_limit, to, value, data, access_list, y_parity, r, s]
                    fields = ["chainId", "nonce", "maxPriorityFeePerGas", "maxFeePerGas", "gas", "to", "value", "data", "accessList", "yParity", "r", "s"]
                    for i, val in enumerate(decoded_rlp):
                        if i < len(fields):
                            name = fields[i]
                            if isinstance(val, bytes):
                                tx_data[name] = to_hex(val)
                            elif isinstance(val, list):
                                tx_data[name] = [to_hex(x) if isinstance(x, bytes) else x for x in val] # Handle access list items if needed
                            else:
                                tx_data[name] = val
                elif tx_type == 1: # EIP-2930
                     # [chainId, nonce, gasPrice, gasLimit, to, value, data, accessList, yParity, r, s]
                    fields = ["chainId", "nonce", "gasPrice", "gas", "to", "value", "data", "accessList", "yParity", "r", "s"]
                    for i, val in enumerate(decoded_rlp):
                        if i < len(fields):
                            name = fields[i]
                            if isinstance(val, bytes):
                                tx_data[name] = to_hex(val)
                            else:
                                tx_data[name] = val
                else:
                    tx_data["raw_rlp"] = [to_hex(x) if isinstance(x, bytes) else x for x in decoded_rlp]

                decoded_items.append({
                    "kind": "SignedTx", 
                    "type": tx_type, 
                    "data": tx_data
                })
            else:
                print(2)
                # Legacy Transaction
                decoded_rlp = rlp.decode(tx_bytes)
                # Legacy format: [nonce, gasPrice, gas, to, value, data, v, r, s]
                fields = ["nonce", "gasPrice", "gas", "to", "value", "data", "v", "r", "s"]
                tx_json = {}
                for i, val in enumerate(decoded_rlp):
                    if i < len(fields):
                        name = fields[i]
                        if isinstance(val, bytes):
                            tx_json[name] = to_hex(val)
                        else:
                            tx_json[name] = val
                
                decoded_items.append({"kind": "SignedTx", "type": "Legacy", "data": tx_json})
            
        except Exception as e:
            print(f"  [Error decoding SignedTx]: {e}")
            decoded_items.append({"kind": "SignedTx", "error": str(e), "raw": tx_bytes.hex()})

        return decoded_items

    return

    # ───────────────────────────────────────────────
    # KIND 0 or 1 = Unsigned or Contract Tx
    # Same format: ABI encoded long payload
    # ───────────────────────────────────────────────
    if kind in (L2MessageKind_UnsignedUserTx, L2MessageKind_ContractTx):
        tx_payload = data[offset:]
        return [{"kind": kind, "unsigned_bytes": tx_payload}]

    # ───────────────────────────────────────────────
    # KIND 3 = Batch
    # Brotli compressed segments
    # ───────────────────────────────────────────────
    if kind == L2MessageKind_Batch:
        segments = []

        while offset < len(data):
            try:
                segment, offset = read_bytestring(data, offset)
            except:
                break

            # Decompress brotli
            decompressed = brotli.decompress(segment)

            # Recursively decode nested messages
            nested = decode_L2Message(decompressed)
            segments.extend(nested)

        return segments

    return [{"kind": kind, "raw": data[offset:]}]


async def listen():
    print(f"Connecting to {FEED_URL}...")
    async with websockets.connect(FEED_URL) as ws:
        print("Connected. Listening...")

        while True:
            raw = await ws.recv()
            msg = json.loads(raw)

            if "messages" not in msg:
                continue

            inner = msg["messages"][0]["message"]["message"]
            l2msg = inner["l2Msg"]
            data = base64.b64decode(l2msg)

            try:
                decoded = decode_L2Message(data)
                if decoded is None:
                    continue
                print("\n========================")
                print("DECODED:")
                for tx in decoded:
                    print(tx)
                print("========================\n")

            except Exception as e:
                print("Decode error:", e)

asyncio.run(listen())
