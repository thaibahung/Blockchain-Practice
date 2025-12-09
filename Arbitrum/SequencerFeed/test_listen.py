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
import csv
from datetime import datetime

# Import DEX swap detection modules
import dex_config
import swap_decoder

FEED_URL = "wss://sepolia-rollup.arbitrum.io/feed"

# Set to False to reduce logging noise
DEBUG = False

# Set to True to only show DEX swap transactions
SWAPS_ONLY = True

# CSV output file for swap data
CSV_OUTPUT_FILE = "dex_swaps.csv"

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

# Global counters for statistics
total_transactions = 0
swap_transactions = 0
decode_errors = 0

def write_swap_to_csv(swap_info: dict, timestamp: str = None):
    """
    Write swap information to CSV file.
    
    Args:
        swap_info: Swap information dictionary
        timestamp: Optional timestamp string
    """
    if not swap_info:
        return
    
    # CSV header - only requested fields
    fieldnames = ['tx_hash', 'pool_address', 'fee_tier', 'token_in', 'token_out', 'version']
    
    # Check if file exists to determine if we need to write header
    import os
    file_exists = os.path.isfile(CSV_OUTPUT_FILE)
    
    try:
        with open(CSV_OUTPUT_FILE, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header if file is new
            if not file_exists:
                writer.writeheader()
            
            # Write swap data - only requested fields
            writer.writerow({
                'tx_hash': swap_info.get('txHash', 'N/A'),
                'pool_address': swap_info.get('poolAddress', 'N/A'),
                'fee_tier': swap_info.get('feeTier', 'N/A'),
                'token_in': swap_info.get('tokenIn', 'N/A'),
                'token_out': swap_info.get('tokenOut', 'N/A'),
                'version': swap_info.get('dexVersion', 'N/A'),
            })
    except Exception as e:
        if DEBUG:
            print(f"Error writing to CSV: {e}")


def analyze_transaction_for_swap(tx_data: dict, tx_hash: str = None) -> dict:
    """
    Analyze a decoded transaction to check if it's a DEX swap.
    
    Args:
        tx_data: Decoded transaction data containing 'to' and 'data' fields
        tx_hash: Transaction hash string (optional)
    
    Returns:
        dict: Swap information if it's a swap, None otherwise
    """
    global swap_transactions
    
    # Check if transaction has required fields
    if not tx_data or 'to' not in tx_data or 'data' not in tx_data:
        return None
    
    to_address = tx_data['to']
    calldata = tx_data['data']

    if to_address not in ["0x3b26d06ea8252a73742d2125d1aceb594ecee5c6",
                          "0x12601ca540436780517a5de8888b4f21a7f39233"]:
        print(to_address)
    
    # Check if the 'to' address is a known DEX router
    if not dex_config.is_dex_router(to_address):
        return None
    
    # Get DEX name
    dex_name = dex_config.get_dex_name(to_address)
    
    # Extract function selector from calldata
    function_selector = swap_decoder.extract_function_selector(calldata)
    
    # Check if it's a known swap function
    if not dex_config.is_swap_function(function_selector):
        if DEBUG:
            print(f"  Unknown function on DEX router: {function_selector}")
        return None
    
    # Decode the swap calldata
    swap_data = swap_decoder.decode_swap_calldata(calldata, function_selector)
    
    if swap_data:
        swap_transactions += 1
        # Format the swap info
        return swap_decoder.format_swap_info(swap_data, dex_name, tx_hash, to_address)
    
    return None

def decode_L2Message(data):
    # Validate data length
    if len(data) < 1:
        print(f"  [Warning: Empty or too small data, length={len(data)}]")
        return []
    
    offset = 0
    kind, offset = read_u8(data, offset)
    decoded_items = []
    
    if DEBUG:
        print(f"  Message Kind: {kind}")

    # ───────────────────────────────────────────────
    # KIND 4 = SignedTx (normal Ethereum signed tx)
    # ───────────────────────────────────────────────
    if kind == L2MessageKind_SignedTx:
        global total_transactions
        total_transactions += 1
        
        if not SWAPS_ONLY:
            print("  -> Type: Signed Transaction")
        
        tx_bytes = data[offset:] # The rest of the data is the RLP encoded tx
        
        # Calculate Transaction Hash
        try:
            tx_hash = Web3.keccak(tx_bytes).hex()
        except Exception as e:
            tx_hash = None
            if DEBUG:
                print(f"  [Error calculating hash]: {e}")
        
        try:
            # Check for Typed Transaction (EIP-2718)
            # If the first byte is in [0, 0x7f], it's a typed tx.
            # Legacy txs start with >= 0xc0 (RLP list)
            
            if len(tx_bytes) == 0:
                 decoded_items.append({"kind": "SignedTx", "error": "Empty transaction bytes"})
                 return decoded_items

            first_byte = tx_bytes[0]
            if first_byte <= 0x7f:
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

                # Check if this is a DEX swap transaction
                swap_info = analyze_transaction_for_swap(tx_data, tx_hash)
                
                tx_item = {
                    "kind": "SignedTx", 
                    "type": tx_type,
                    "hash": tx_hash,
                    "data": tx_data
                }
                
                # Add swap info if detected
                if swap_info:
                    tx_item["swap"] = swap_info
                    if not SWAPS_ONLY:
                        print(f" DEX SWAP DETECTED: {swap_info['dex']}")
                
                # Only add to results if not filtering or if it's a swap
                if not SWAPS_ONLY or swap_info:
                    decoded_items.append(tx_item)
                    
            else:
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
                
                # Check if this is a DEX swap transaction
                swap_info = analyze_transaction_for_swap(tx_json, tx_hash)
                
                tx_item = {
                    "kind": "SignedTx", 
                    "type": "Legacy",
                    "hash": tx_hash,
                    "data": tx_json
                }
                
                # Add swap info if detected
                if swap_info:
                    tx_item["swap"] = swap_info
                    if not SWAPS_ONLY:
                        print(f"DEX SWAP DETECTED: {swap_info['dex']}")
                
                # Only add to results if not filtering or if it's a swap
                if not SWAPS_ONLY or swap_info:
                    decoded_items.append(tx_item)
            
        except Exception as e:
            global decode_errors
            decode_errors += 1
            if DEBUG:
                print(f"  [Error decoding SignedTx]: {e}")
            decoded_items.append({"kind": "SignedTx", "error": str(e), "raw": tx_bytes.hex()})

        return decoded_items

    # ───────────────────────────────────────────────
    # KIND 3 = Batch
    # Can be brotli compressed or raw transactions
    # ───────────────────────────────────────────────
    if kind == L2MessageKind_Batch:
        if DEBUG:
            print("  -> Type: Batch")
            print(f"  Batch data length: {len(data) - offset}")
        segments = []

        # Check if the batch is empty
        if offset >= len(data):
            if DEBUG:
                print("  Empty batch")
            return []
        
        # Try to read as length-prefixed brotli segments first
        temp_offset = offset
        try:
            while temp_offset < len(data):
                segment, temp_offset = read_bytestring(data, temp_offset)
                
                # Skip empty or too-small segments
                if len(segment) < 1:
                    if DEBUG:
                        print(f"  Skipping empty segment")
                    continue
                
                # Try to decompress with brotli
                try:
                    decompressed = brotli.decompress(segment)
                    if DEBUG:
                        print(f"  Decompressed {len(segment)} -> {len(decompressed)} bytes")
                    
                    # Recursively decode nested messages
                    nested = decode_L2Message(decompressed)
                    if nested:
                        segments.extend(nested)
                except Exception as e:
                    # Not brotli compressed, treat as raw data
                    if DEBUG:
                        print(f"  Segment not brotli-compressed (len={len(segment)}), trying as raw L2 message")
                    try:
                        nested = decode_L2Message(segment)
                        if nested:
                            segments.extend(nested)
                    except Exception as e2:
                        if DEBUG:
                            print(f"  [Skipping invalid segment]: {str(e2)[:50]}")
            
            if segments:
                return segments
        except Exception as e:
            print(f"  [Could not parse as segmented batch]: {e}")
        
        # If segmented parsing failed, try treating remaining data as single raw message
        try:
            nested = decode_L2Message(data[offset:])
            if nested:
                return nested
        except Exception as e:
            print(f"  [Error decoding as single raw message]: {e}")
        
        # Return empty if all parsing attempts failed
        return []

    # Unknown or other kinds
    return []



async def listen():
    print(f"Connecting to {FEED_URL}...")
    
    async with websockets.connect(FEED_URL) as ws:
        print("Connected. Listening for transactions...\n")

        message_count = 0
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
                if not decoded:
                    continue
                
                message_count += 1
                
                # Display swap transactions with formatted output
                for tx in decoded:
                    if "swap" in tx:
                        swap = tx["swap"]
                        
                        # Write to CSV
                        write_swap_to_csv(swap)
                        
                        # Print to console
                        print("\n" + "=" * 60)
                        print(f"DEX SWAP DETECTED!")
                        print(f"  DEX:       {swap['dex']}")
                        print(f"  Version:   {swap.get('dexVersion', 'Unknown')}")
                        print(f"  Function:  {swap['function']}")
                        print(f"  Tx Hash:   {swap.get('txHash', 'N/A')}")
                        print(f"  Pool:      {swap.get('poolAddress', 'Unknown')}")
                        print(f"  Fee Tier:  {swap.get('feeTier', 'N/A')}")
                        print(f"  Token In:  {swap.get('tokenIn', 'N/A')}")
                        print(f"  Token Out: {swap.get('tokenOut', 'N/A')}")
                        print(f"  Amount In: {swap.get('amountIn', 'N/A')}")
                        print(f"  Min Out:   {swap.get('amountOutMin', 'N/A')}")
                        if 'path' in swap and isinstance(swap['path'], list) and len(swap['path']) > 2:
                            print(f"  Path:      {' -> '.join(swap['path'])}")
                        print("=" * 60)
                    elif not SWAPS_ONLY:
                        print(f"\n[Transaction {total_transactions}]")
                        print(tx)
                
                # Periodic statistics (every 50 messages)
                if message_count % 50 == 0:
                    print(f"\nStats: {total_transactions} txs | {swap_transactions} swaps | {decode_errors} errors")

            except Exception as e:
                if DEBUG:
                    print("Decode error:", e)

asyncio.run(listen())
