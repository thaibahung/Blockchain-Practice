"""
Swap Decoder Module for Arbitrum DEX Transactions

Decodes swap transaction calldata to extract token pairs, amounts, and other details.
"""

from eth_abi import decode as abi_decode
from typing import Dict, Optional, List


def extract_function_selector(calldata: str) -> str:
    """
    Extract the 4-byte function selector from calldata.
    
    Args:
        calldata: Transaction calldata (hex string with or without 0x prefix)
    
    Returns:
        str: 4-byte function selector (with 0x prefix)
    """
    if not calldata:
        return ""
    
    # Remove 0x prefix if present
    if calldata.startswith("0x"):
        calldata = calldata[2:]
    
    # First 8 hex characters = 4 bytes
    if len(calldata) < 8:
        return ""
    
    return "0x" + calldata[:8]


def decode_exact_input_single(calldata: str) -> Optional[Dict]:
    """
    Decode exactInputSingle swap function.
    
    Function signature:
    exactInputSingle((address tokenIn, address tokenOut, uint24 fee, 
                      address recipient, uint256 amountIn, uint256 amountOutMinimum, 
                      uint160 sqrtPriceLimitX96))
    
    Args:
        calldata: Transaction calldata (hex string)
    
    Returns:
        Dict with swap details or None if decoding fails
    """
    try:
        # Remove function selector (first 4 bytes = 8 hex chars)
        if calldata.startswith("0x"):
            calldata = calldata[2:]
        
        params_data = calldata[8:]  # Skip function selector
        
        # Decode the tuple parameter
        # Types: address, address, uint24, address, uint256, uint256, uint160
        decoded = abi_decode(
            ['address', 'address', 'uint24', 'address', 'uint256', 'uint256', 'uint160'],
            bytes.fromhex(params_data)
        )
        
        return {
            "function": "exactInputSingle",
            "tokenIn": decoded[0],
            "tokenOut": decoded[1],
            "fee": decoded[2],
            "recipient": decoded[3],
            "amountIn": decoded[4],
            "amountOutMinimum": decoded[5],
            "sqrtPriceLimitX96": decoded[6]
        }
    except Exception as e:
        return None


def decode_exact_input(calldata: str) -> Optional[Dict]:
    """
    Decode exactInput swap function (multi-hop).
    
    Function signature:
    exactInput((bytes path, address recipient, uint256 amountIn, uint256 amountOutMinimum))
    
    Args:
        calldata: Transaction calldata (hex string)
    
    Returns:
        Dict with swap details or None if decoding fails
    """
    try:
        if calldata.startswith("0x"):
            calldata = calldata[2:]
        
        params_data = calldata[8:]
        
        # Decode the tuple parameter
        decoded = abi_decode(
            ['bytes', 'address', 'uint256', 'uint256'],
            bytes.fromhex(params_data)
        )
        
        path_bytes = decoded[0]
        
        # Parse the encoded path to extract token addresses
        # Path format: tokenA (20 bytes) + fee (3 bytes) + tokenB (20 bytes) + ...
        tokens = []
        offset = 0
        while offset < len(path_bytes):
            if offset + 20 <= len(path_bytes):
                token = "0x" + path_bytes[offset:offset+20].hex()
                tokens.append(token)
                offset += 20
                # Skip fee (3 bytes) if not at the end
                if offset + 3 <= len(path_bytes):
                    offset += 3
            else:
                break
        
        return {
            "function": "exactInput",
            "tokens": tokens,
            "tokenIn": tokens[0] if tokens else None,
            "tokenOut": tokens[-1] if len(tokens) > 1 else None,
            "recipient": decoded[1],
            "amountIn": decoded[2],
            "amountOutMinimum": decoded[3],
            "path": path_bytes.hex()
        }
    except Exception as e:
        return None


def decode_swap_exact_tokens_for_tokens(calldata: str) -> Optional[Dict]:
    """
    Decode swapExactTokensForTokens function (Uniswap V2 style).
    
    Function signature:
    swapExactTokensForTokens(uint256 amountIn, uint256 amountOutMin, 
                             address[] path, address to, uint256 deadline)
    
    Args:
        calldata: Transaction calldata (hex string)
    
    Returns:
        Dict with swap details or None if decoding fails
    """
    try:
        if calldata.startswith("0x"):
            calldata = calldata[2:]
        
        params_data = calldata[8:]
        
        # Decode parameters
        decoded = abi_decode(
            ['uint256', 'uint256', 'address[]', 'address', 'uint256'],
            bytes.fromhex(params_data)
        )
        
        path = decoded[2]
        
        return {
            "function": "swapExactTokensForTokens",
            "amountIn": decoded[0],
            "amountOutMin": decoded[1],
            "path": path,
            "tokenIn": path[0] if path else None,
            "tokenOut": path[-1] if len(path) > 1 else None,
            "recipient": decoded[3],
            "deadline": decoded[4]
        }
    except Exception as e:
        return None


def decode_swap_calldata(calldata: str, function_selector: str) -> Optional[Dict]:
    """
    Main function to decode swap calldata based on function selector.
    
    Args:
        calldata: Transaction calldata (hex string)
        function_selector: 4-byte function selector
    
    Returns:
        Dict with decoded swap details or None if decoding fails
    """
    # Normalize function selector
    if not function_selector.startswith("0x"):
        function_selector = "0x" + function_selector
    
    function_selector = function_selector.lower()
    
    # Route to appropriate decoder
    if function_selector == "0x414bf389":  # exactInputSingle
        return decode_exact_input_single(calldata)
    
    elif function_selector == "0xc04b8d59":  # exactInput
        return decode_exact_input(calldata)
    
    elif function_selector == "0x38ed1739":  # swapExactTokensForTokens
        return decode_swap_exact_tokens_for_tokens(calldata)
    
    # Add more decoders as needed for other function types
    
    return None


def format_swap_info(swap_data: Dict, dex_name: str, tx_hash: str = None, to_address: str = None) -> Dict:
    """
    Format decoded swap data into a clean, standardized structure.
    
    Args:
        swap_data: Decoded swap data from decode_swap_calldata
        dex_name: Name of the DEX (e.g., "Uniswap V3")
        tx_hash: Transaction hash (optional)
        to_address: Router address for DEX version lookup (optional)
    
    Returns:
        Dict with formatted swap information
    """
    if not swap_data:
        return None
    
    # Import here to avoid circular dependency
    import dex_config
    import pool_helper
    
    result = {
        "dex": dex_name,
        "function": swap_data.get("function", "Unknown"),
        "tokenIn": swap_data.get("tokenIn"),
        "tokenOut": swap_data.get("tokenOut"),
        "amountIn": swap_data.get("amountIn"),
    }
    
    # Add DEX version
    if to_address:
        result["dexVersion"] = dex_config.get_dex_version(to_address)
    else:
        result["dexVersion"] = "Unknown"
    
    # Add fee tier (for V3 swaps)
    if "fee" in swap_data:
        result["feeTier"] = swap_data["fee"]

    
    # Add amountOut based on function type
    if "amountOutMinimum" in swap_data:
        result["amountOutMin"] = swap_data["amountOutMinimum"]
    elif "amountOutMin" in swap_data:
        result["amountOutMin"] = swap_data["amountOutMin"]
    
    # Add transaction hash if available
    if tx_hash:
        result["txHash"] = tx_hash
    
    # Add path for multi-hop swaps
    if "path" in swap_data and isinstance(swap_data["path"], list):
        result["path"] = swap_data["path"]
    elif "tokens" in swap_data:
        result["path"] = swap_data["tokens"]
    
    # Compute pool address
    token_in = result.get("tokenIn")
    token_out = result.get("tokenOut")
    fee_tier = result.get("feeTier")
    dex_version = result.get("dexVersion", "Unknown")
    
    if token_in and token_out:
        pool_address = pool_helper.get_pool_address(token_in, token_out, fee_tier, dex_version)
        result["poolAddress"] = pool_address
    else:
        result["poolAddress"] = "Unknown"
    
    return result

