"""Domain entities for the arbitrage detection system."""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, Tuple, Optional, List, Set, Literal, Any, Union
import time
import math

from networkx import network_simplex

@dataclass
class TokenInfo:
    """Information about a token."""
    id: str
    symbol: str
    decimals: int


@dataclass
class PairInfo:
    """Information about a trading pair."""
    token0: TokenInfo
    token1: TokenInfo
    reserve_usd: float

@dataclass
class SwapResult:
    """Slippage estimation for a swap."""
    amount_in: int
    amount_out: int
    price_before: Decimal
    price_after: Decimal
    slippage_percent: Decimal


# Base Pool Event classes

@dataclass
class PoolEvent:
    """Base class for pool events."""
    pool_address: str
    block_number: int
    event_type: Literal['swap', 'mint', 'burn', 'sync']
    timestamp: float = field(default_factory=time.time)
    is_reorg: bool = False
    transaction_hash: str = ""
    log_index: int = 0
    
    def get_event_id(self) -> str:
        """
        Get a unique identifier for this event.
        
        Returns:
            A string that uniquely identifies this event
        """
        # Create a unique ID using pool address, event type, tx hash, and log index
        return f"{self.pool_address}_{self.event_type}_{self.transaction_hash}_{self.log_index}"


# V2 Pool Event classes

@dataclass
class V2PoolEvent(PoolEvent):
    """Base class for Uniswap V2 pool events."""
    
    @property
    def pool_type(self) -> str:
        """Get the pool type."""
        return 'v2'

@dataclass
class V2Swap(V2PoolEvent):
    """Represents a swap event in a Uniswap V2 pool."""
    # All fields are optional with defaults
    amount0_in: int = 0
    amount1_in: int = 0
    amount0_out: int = 0
    amount1_out: int = 0
    
    def __post_init__(self):
        """Initialize the event_type field."""
        self.event_type = 'swap'

@dataclass
class V2Mint(V2PoolEvent):
    """Represents a mint (add liquidity) event in a Uniswap V2 pool."""
    amount0: int = 0
    amount1: int = 0
    
    def __post_init__(self):
        """Initialize the event_type field."""
        self.event_type = 'mint'

@dataclass
class V2Burn(V2PoolEvent):
    """Represents a burn (remove liquidity) event in a Uniswap V2 pool."""
    amount0: int = 0
    amount1: int = 0
    
    def __post_init__(self):
        """Initialize the event_type field."""
        self.event_type = 'burn'

@dataclass
class V2Sync(V2PoolEvent):
    """Represents a sync event in a Uniswap V2 pool."""
    reserve0: int = 0
    reserve1: int = 0
    
    def __post_init__(self):
        """Initialize the event_type field."""
        self.event_type = 'sync'

@dataclass
class CexTradingPair:
    """Trading pair information for centralized exchanges."""
    symbol: str
    base_asset: str
    quote_asset: str
    volume_24h: Decimal
    liquidity_usd: Decimal
    price: Decimal
    min_price: Decimal
    max_price: Decimal
    tick_size: Decimal
    min_qty: Decimal
    max_qty: Decimal
    step_size: Decimal

@dataclass
class DexTradingPair:
    """Trading pair information for decentralized exchanges."""
    pair_address: str
    token0_address: str
    token0_symbol: str
    token0_derivedETH: Decimal
    token0_decimals: int
    token1_address: str
    token1_symbol: str
    token1_derivedETH: Decimal
    token1_decimals: int
    total_liquidity_usd: Decimal
    volume_24h: Decimal
    fee_tier: int # Fee tier in basis points (e.g., 3000 for 0.3%)
    reserve0: Decimal
    reserve1: Decimal
    token0_price: Decimal  # token0 per token1
    token1_price: Decimal  # token1 per token0
    network: str  # Network name (e.g., Ethereum, Binance Smart Chain)
    block_number: int = 0  # Block number at which the data was fetched
    protocol: str = "" # Protocol identifier (e.g., Uniswap V2, Uniswap V3, etc.)

@dataclass
class TradingPairFilter:
    """Filter options for trading pairs."""
    min_liquidity_usd: Optional[Decimal] = None
    min_volume_24h: Optional[Decimal] = None
    assets: Optional[set[str]] = None


@dataclass
class Transaction:
    """Represents an transaction."""
    hash: str
    to: str
    from_address: str
    input_data: str
    value: int
    gas: int
    gas_price: Optional[int] = None
    maxPriorityFeePerGas: Optional[int] = None
    maxFeePerGas: Optional[int] = None
    nonce: Optional[int] = None
    v: Optional[int] = None
    r: Optional[str] = None
    s: Optional[str] = None