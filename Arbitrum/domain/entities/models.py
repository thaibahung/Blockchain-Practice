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