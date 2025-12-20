"""
DEX Configuration Module for Arbitrum

Contains router addresses and function signatures for major DEXes on:
- Arbitrum One mainnet
- Arbitrum Sepolia testnet

Used for identifying and decoding swap transactions from SequencerFeed.
"""

# --------------------------------------------------------------------------------------
# Major DEX Router Addresses on Arbitrum (lowercase for comparison)
# Note: Uniswap V2/V3 and Universal Router reuse the same addresses across
#       Arbitrum One (42161) and Arbitrum Sepolia (421614).
# --------------------------------------------------------------------------------------

DEX_ROUTERS = {
    # -----------------
    # Uniswap V3 Routers
    # -----------------
    # SwapRouter02
    "0xe592427a0aece92de3edee1f18e0157c05861564": "Uniswap V3 Router 1",
    "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45": "Uniswap V3 Router 2",
    "0x101F443B4d1b059569D643917553c771E1b9663E": "Arbitrum Sepolia Uniswap V3 Router",

    # Universal Router (v4 routing entrypoint – used for v2/v3 under the hood)
    "0xa51afafe0263b40edaef0df8781ea9aa03e381a3": "Uniswap Universal Router",

    # -------------
    # Sushiswap (V2)
    # -------------
    "0x1b02da8cb0d097eb8d57a175b88c7d8b47997506": "Sushiswap Router",
    "0xf2614a233c7c3e7f08b1f887ba133a13f1eb2c55": "Sushiswap Router 2",

    # -------------
    # Uniswap V2
    # -------------
    # Same address on Arbitrum One + Arbitrum Sepolia
    "0x4752ba5dbc23f44d87826276bf6fd6b1c372ad24": "Uniswap V2 Router",


    # -------------
    # Camelot
    # -------------
    # Arbitrum One mainnet router
    "0xc873fecbd354f5a56e00e710b90ef4201db2448d": "Camelot Router (Arbitrum One)",

    # Arbitrum Sepolia testnet router
    "0x171b925c51565f5d2a7d8c494ba3188d304efd93": "Camelot Router (Arbitrum Sepolia)",
}

# --------------------------------------------------------------------------------------
# Swap Function Signatures (4-byte selector)
# --------------------------------------------------------------------------------------

SWAP_SIGNATURES = {
    # --------------------------
    # Uniswap V3 SwapRouter funcs
    # --------------------------
    "0x414bf389": "exactInputSingle",      # exactInputSingle((address,address,uint24,address,uint256,uint256,uint160))
    "0xc04b8d59": "exactInput",            # exactInput((bytes,address,uint256,uint256))
    "0xdb3e2198": "exactOutputSingle",     # exactOutputSingle((address,address,uint24,address,uint256,uint256,uint160))
    "0xf28c0498": "exactOutput",           # exactOutput((bytes,address,uint256,uint256))

    # ------------------------------------------------
    # Uniswap V2-style swaps (used by Sushi, Camelot V2, etc.)
    # ------------------------------------------------
    "0x38ed1739": "swapExactTokensForTokens",           # swapExactTokensForTokens(uint256,uint256,address[],address,uint256)
    "0x8803dbee": "swapTokensForExactTokens",           # swapTokensForExactTokens(uint256,uint256,address[],address,uint256)
    "0x7ff36ab5": "swapExactETHForTokens",              # swapExactETHForTokens(uint256,address[],address,uint256)
    "0x4a25d94a": "swapTokensForExactETH",              # swapTokensForExactETH(uint256,uint256,address[],address,uint256)
    "0x18cbafe5": "swapExactTokensForETH",              # swapExactTokensForETH(uint256,uint256,address[],address,uint256)
    "0xfb3bdb41": "swapETHForExactTokens",              # swapETHForExactTokens(uint256,address[],address,uint256)

    # --- Fee-on-transfer variants (Uniswap V2 Router02) ---
    # swapExactTokensForTokensSupportingFeeOnTransferTokens(uint256,uint256,address[],address,uint256)
    "0x5c11d795": "swapExactTokensForTokensSupportingFeeOnTransferTokens",
    # swapExactETHForTokensSupportingFeeOnTransferTokens(uint256,address[],address,uint256)
    "0xb6f9de95": "swapExactETHForTokensSupportingFeeOnTransferTokens",
    # swapExactTokensForETHSupportingFeeOnTransferTokens(uint256,uint256,address[],address,uint256)
    "0x791ac947": "swapExactTokensForETHSupportingFeeOnTransferTokens",

    # ---------------
    # Universal Router
    # ---------------
    "0x24856bc3": "execute",               # execute(bytes,bytes[],uint256)
    "0x3593564c": "execute",               # execute(bytes,bytes[])
}

# --------------------------------------------------------------------------------------
# DEX Version Mapping (router address -> version)
# --------------------------------------------------------------------------------------

DEX_VERSIONS = {
    # Uniswap V3 (SwapRouter02 + Universal Router entry)
    "0xe592427a0aece92de3edee1f18e0157c05861564": "Uniswap V3",
    "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45": "Uniswap V3",
    "0xa51afafe0263b40edaef0df8781ea9aa03e381a3": "Uniswap V4 Universal Router",  # routes v2/v3/v3
    "0x101F443B4d1b059569D643917553c771E1b9663E": "Uniswap V3",

    # Uniswap V2
    "0x4752ba5dbc23f44d87826276bf6fd6b1c372ad24": "Uniswap V2",

    # Sushiswap V2
    "0x1b02da8cb0d097eb8d57a175b88c7d8b47997506": "Sushiswap V2",
    "0xf2614a233c7c3e7f08b1f887ba133a13f1eb2c55": "Sushiswap V2",

    # Camelot
    "0xc873fecbd354f5a56e00e710b90ef4201db2448d": "Camelot V2",
    "0x171b925c51565f5d2a7d8c494ba3188d304efd93": "Camelot V3 (Algebra)",
}


def _normalize_address(address: str) -> str:
    """
    Normalize an Ethereum address to lowercase with 0x prefix.

    Accepts:
        - with/without 0x prefix
        - mixed case

    Returns:
        normalized address string or empty string if invalid.
    """
    if not address:
        return ""

    addr = address.lower()
    if not addr.startswith("0x"):
        addr = "0x" + addr

    return addr


def is_dex_router(address: str) -> bool:
    """
    Check if an address is a known DEX router (mainnet or Arbitrum Sepolia).
    
    Args:
        address: Ethereum address (with or without 0x prefix)
    
    Returns:
        bool: True if address is a known DEX router
    """
    normalized = _normalize_address(address)
    if not normalized:
        return False

    return normalized in DEX_ROUTERS


def get_dex_name(address: str) -> str:
    """
    Get the DEX name for a router address.
    
    Args:
        address: Ethereum address (with or without 0x prefix)
    
    Returns:
        str: DEX name or "Unknown DEX" if not found
    """
    normalized = _normalize_address(address)
    if not normalized:
        return "Unknown DEX"
    
    return DEX_ROUTERS.get(normalized, "Unknown DEX")


def get_function_name(selector: str) -> str:
    """
    Get the function name for a 4-byte function selector.
    
    Args:
        selector: 4-byte function selector (with or without 0x prefix)
    
    Returns:
        str: Function name or "Unknown" if not found
    """
    if not selector:
        return "Unknown"
    
    # Normalize selector to lowercase with 0x prefix
    normalized = selector.lower()
    if not normalized.startswith("0x"):
        normalized = "0x" + normalized
    
    # Ensure it's exactly 10 characters (0x + 8 hex chars)
    if len(normalized) > 10:
        normalized = normalized[:10]
    
    return SWAP_SIGNATURES.get(normalized, "Unknown")


def get_dex_version(address: str) -> str:
    """
    Get the DEX version for a router address.
    
    Args:
        address: Ethereum address (with or without 0x prefix)
    
    Returns:
        str: DEX version (e.g., "Uniswap V3", "Sushiswap V2") or "Unknown"
    """
    normalized = _normalize_address(address)
    if not normalized:
        return "Unknown"
    
    return DEX_VERSIONS.get(normalized, "Unknown")


def is_swap_function(selector: str) -> bool:
    """
    Check if a function selector is a known swap function.
    
    Args:
        selector: 4-byte function selector (with or without 0x prefix)
    
    Returns:
        bool: True if selector is a known swap function
    """
    return get_function_name(selector) != "Unknown"
