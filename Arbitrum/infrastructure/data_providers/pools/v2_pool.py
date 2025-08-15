""" Uniswap V2 Pool Implementation """

from decimal import Decimal
import decimal
import math
from typing import Optional, Tuple

from domain.entities.pool_models import IV2Pool

class V2Pool(IV2Pool):
    def __init__(
        self,
        address: str,
        token0: str,
        token1: str,
        reserve0: int,
        reserve1: int,
        fee: float = 0.003,  # Default fee is 0.3%
        decimals0: int = 18,
        decimals1: int = 18,
        protocol: str = "uniswap_v2"
    ):
        """
        Initialize a V2 pool.
        
        Args:
            address: Pool contract address
            token0: Address of token0
            token1: Address of token1
            reserve0: Reserve of token0 in wei units
            reserve1: Reserve of token1 in wei units
            fee: Fee percentage as a decimal (e.g., 0.003 for 0.3%)
            decimals0: Decimals for token0 (default: 18)
            decimals1: Decimals for token1 (default: 18)
        """
        self._address = address
        self._token0 = token0
        self._token1 = token1
        self._reserve0 =  reserve0
        self._reserve1 =  reserve1
        self._fee = fee
        self._decimals0 = decimals0
        self._decimals1 = decimals1
        self._fee_pct = fee  # For compatibility with SimulatedV2Pool
        self._protocol = protocol
        
        # Pre-calculate fee multiplier for integer arithmetic (fee as parts per 10000)
        self._fee_multiplier = int((1 - fee) * 10000)  # e.g., 9970 for 0.3% fee

    @property
    def protocol(self) -> str:
        """Get the protocol name."""
        return self._protocol
    
    property
    def decimals0(self) -> int:
        """Get the decimals for token0."""
        return self._decimals0
    
    @property
    def decimals1(self) -> int:
        """Get the decimals for token1."""
        return self._decimals1
    
    @property
    def address(self) -> str:
        """Get the pool contract address."""
        return self._address
    
    @property
    def token0(self) -> str:
        """Get the address of token0."""
        return self._token0
    
    @property
    def token1(self) -> str:
        """Get the address of token1."""
        return self._token1
    
    @property
    def reserve0(self) -> int:
        """Get the reserve of token0 in wei units."""
        return self._reserve0
    
    @property
    def reserve1(self) -> int:
        """Get the reserve of token1 in wei units."""
        return self._reserve1
    
    def get_price(self) -> Decimal:
        """
        Get the current price (token1/token0).
        
        Returns:
            Current price as token1/token0
        """
        if self._reserve0 == 0:
            return Decimal('0')
        
        return (Decimal(self._reserve1) / Decimal(self._reserve0)) / Decimal(10 ** (self.decimals1 - self.decimals0))
    
    @property
    def price0(self) -> Decimal:
        """Price of token0 in terms of token1."""
        if self._reserve0 == 0:
            return Decimal(0)
        return (Decimal(self._reserve1) / Decimal(self._reserve0)) / Decimal(10 ** (self.decimals1 - self.decimals0))
    
    @property
    def price1(self) -> Decimal:
        """Price of token1 in terms of token0."""
        if self._reserve1 == 0:
            return Decimal(0)
        return (Decimal(self._reserve0) / Decimal(self._reserve1)) / Decimal(10 ** (self.decimals0 - self.decimals1))
    
    @property
    def fee(self) -> float:
        """Get the fee as a decimal (e.g., 0.003 for 0.3%)."""
        return self._fee