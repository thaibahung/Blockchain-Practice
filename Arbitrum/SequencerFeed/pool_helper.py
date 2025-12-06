"""
Pool Helper Module

Computes pool addresses for Uniswap V3 and V2-style DEXes.
"""

from web3 import Web3
import eth_abi

# Uniswap V3 Factory on Arbitrum
UNISWAP_V3_FACTORY = "0x1F98431c8aD98523631AE4a59f267346ea31F984"

# Uniswap V3 Pool Init Code Hash
UNISWAP_V3_INIT_CODE_HASH = "0xe34f199b19b2b4f47f68442619d555527d244f78a3297ea89325f843f87b8b54"

# Sushiswap V2 Factory on Arbitrum
SUSHISWAP_V2_FACTORY = "0xc35DADB65012eC5796536bD9864eD8773aBc74C4"

# Sushiswap V2 Init Code Hash
SUSHISWAP_V2_INIT_CODE_HASH = "0xe18a34eb0e04b04f7a0ac29a6e80748dca96319b42c54d679cb821dca90c6303"


def compute_v3_pool_address(token0: str, token1: str, fee: int) -> str:
    """
    Compute Uniswap V3 pool address using CREATE2.
    
    Args:
        token0: First token address (should be < token1)
        token1: Second token address
        fee: Fee tier (e.g., 500, 3000, 10000)
    
    Returns:
        str: Pool address
    """
    # Normalize addresses
    token0 = Web3.to_checksum_address(token0)
    token1 = Web3.to_checksum_address(token1)
    
    # Sort tokens (token0 < token1)
    if int(token0, 16) > int(token1, 16):
        token0, token1 = token1, token0
    
    # Encode the salt: keccak256(abi.encodePacked(token0, token1, fee))
    salt = Web3.keccak(
        eth_abi.encode(
            ['address', 'address', 'uint24'],
            [token0, token1, fee]
        )
   )
    
   # Compute CREATE2 address
    # address = keccak256(0xff ++ factory ++ salt ++ initCodeHash)[12:]
    data = b'\xff' + bytes.fromhex(UNISWAP_V3_FACTORY[2:]) + salt + bytes.fromhex(UNISWAP_V3_INIT_CODE_HASH[2:])
    pool_address = Web3.keccak(data)[12:]  # Take last 20 bytes
    
    return Web3.to_checksum_address('0x' + pool_address.hex())


def compute_v2_pool_address(token0: str, token1: str, factory: str = SUSHISWAP_V2_FACTORY, init_code_hash: str = SUSHISWAP_V2_INIT_CODE_HASH) -> str:
    """
    Compute Uniswap V2-style pool address using CREATE2.
    
    Args:
        token0: First token address
        token1: Second token address
        factory: Factory contract address
        init_code_hash: Init code hash for the factory
    
    Returns:
        str: Pool address
    """
    # Normalize addresses
    token0 = Web3.to_checksum_address(token0)
    token1 = Web3.to_checksum_address(token1)
    
    # Sort tokens (token0 < token1)
    if int(token0, 16) > int(token1, 16):
        token0, token1 = token1, token0
    
    # Encode the salt: keccak256(abi.encodePacked(token0, token1))
    salt = Web3.keccak(
        bytes.fromhex(token0[2:]) + bytes.fromhex(token1[2:])
    )
    
    # Compute CREATE2 address
    data = b'\xff' + bytes.fromhex(factory[2:]) + salt + bytes.fromhex(init_code_hash[2:])
    pool_address = Web3.keccak(data)[12:]  # Take last 20 bytes
    
    return Web3.to_checksum_address('0x' + pool_address.hex())


def get_pool_address(token_in: str, token_out: str, fee: int = None, dex_version: str = "Unknown") -> str:
    """
    Get pool address based on DEX version and parameters.
    
    Args:
        token_in: Input token address
        token_out: Output token address
        fee: Fee tier (for V3), can be None for V2
        dex_version: DEX version string (e.g., "Uniswap V3", "Sushiswap V2")
    
    Returns:
        str: Pool address or "Unknown" if cannot compute
    """
    try:
        if "V3" in dex_version:
            if fee is None:
                return "Unknown"
            return compute_v3_pool_address(token_in, token_out, fee)
        elif "V2" in dex_version or "Sushiswap" in dex_version:
            return compute_v2_pool_address(token_in, token_out)
        else:
            return "Unknown"
    except Exception as e:
        return "Unknown"
