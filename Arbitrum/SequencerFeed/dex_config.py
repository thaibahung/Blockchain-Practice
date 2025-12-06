"""
DEX Configuration Module for Arbitrum

Contains router addresses and function signatures for major DEXes on Arbitrum.
Used for identifying and decoding swap transactions from SequencerFeed.
"""

# Major DEX Router Addresses on Arbitrum (lowercase for comparison)
DEX_ROUTERS = {
    # Uniswap V3
    "0xe592427a0aece92de3edee1f18e0157c05861564": "Uniswap V3 Router 1",
    "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45": "Uniswap V3 Router 2",
    "0xa51afafe0263b40edaef0df8781ea9aa03e381a3": "Uniswap Universal Router",
    
    # Sushiswap
    "0x1b02da8cb0d097eb8d57a175b88c7d8b47997506": "Sushiswap Router",
    "0xf2614a233c7c3e7f08b1f887ba133a13f1eb2c55": "Sushiswap Router 2",

    # Uniswap V2
    "0x4752ba5dbc23f44d87826276bf6fd6b1c372ad24": "Uniswap V2 Router",
    
    # Camelot (will add more as discovered)
    # Note: Camelot addresses may vary, add as needed
}

# Swap Function Signatures (4-byte selector)
SWAP_SIGNATURES = {
    # Uniswap V3 SwapRouter functions
    "0x414bf389": "exactInputSingle",      # exactInputSingle((address,address,uint24,address,uint256,uint256,uint160))
    "0xc04b8d59": "exactInput",            # exactInput((bytes,address,uint256,uint256))
    "0xdb3e2198": "exactOutputSingle",     # exactOutputSingle((address,address,uint24,address,uint256,uint256,uint160))
    "0xf28c0498": "exactOutput",           # exactOutput((bytes,address,uint256,uint256))
    
    # Uniswap V2 style (used by Sushiswap, etc.)
    "0x38ed1739": "swapExactTokensForTokens",           # swapExactTokensForTokens(uint256,uint256,address[],address,uint256)
    "0x8803dbee": "swapTokensForExactTokens",           # swapTokensForExactTokens(uint256,uint256,address[],address,uint256)
    "0x7ff36ab5": "swapExactETHForTokens",              # swapExactETHForTokens(uint256,address[],address,uint256)
    "0x4a25d94a": "swapTokensForExactETH",              # swapTokensForExactETH(uint256,uint256,address[],address,uint256)
    "0x18cbafe5": "swapExactTokensForETH",              # swapExactTokensForETH(uint256,uint256,address[],address,uint256)
    "0xfb3bdb41": "swapETHForExactTokens",              # swapETHForExactTokens(uint256,address[],address,uint256)
    
    # Universal Router
    "0x24856bc3": "execute",                            # execute(bytes,bytes[],uint256)
    "0x3593564c": "execute",                            # execute(bytes,bytes[])
}

# DEX Version Mapping (router address -> version)
DEX_VERSIONS = {
    # Uniswap V3
    "0xe592427a0aece92de3edee1f18e0157c05861564": "Uniswap V3",
    "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45": "Uniswap V3",
    "0xa51afafe0263b40edaef0df8781ea9aa03e381a3": "Uniswap V3",

    # Uniswap V2
    "0x4752ba5dbc23f44d87826276bf6fd6b1c372ad24": "Uniswap V2",
    
    # Sushiswap V2
    "0x1b02da8cb0d097eb8d57a175b88c7d8b47997506": "Sushiswap V2",
    "0xf2614a233c7c3e7f08b1f887ba133a13f1eb2c55": "Sushiswap V2",
}



def is_dex_router(address: str) -> bool:
    """
    Check if an address is a known DEX router.
    
    Args:
        address: Ethereum address (with or without 0x prefix)
    
    Returns:
        bool: True if address is a known DEX router
    """
    if not address:
        return False
    
    # Normalize address to lowercase, remove 0x prefix
    normalized = address.lower()
    if normalized.startswith("0x"):
        normalized = normalized[2:]
    
    # Add back 0x for comparison
    normalized = "0x" + normalized
    
    return normalized in DEX_ROUTERS


def get_dex_name(address: str) -> str:
    """
    Get the DEX name for a router address.
    
    Args:
        address: Ethereum address (with or without 0x prefix)
    
    Returns:
        str: DEX name or "Unknown DEX" if not found
    """
    if not address:
        return "Unknown DEX"
    
    # Normalize address
    normalized = address.lower()
    if normalized.startswith("0x"):
        normalized = normalized[2:]
    normalized = "0x" + normalized
    
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
    if not address:
        return "Unknown"
    
    # Normalize address
    normalized = address.lower()
    if normalized.startswith("0x"):
        normalized = normalized[2:]
    normalized = "0x" + normalized
    
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
