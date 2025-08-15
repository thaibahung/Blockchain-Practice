from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, List, Tuple, Optional, Any

class IPool(ABC):
    """Base interface for all pool types."""
    
    @property
    @abstractmethod
    def address(self) -> str:
        """Get the pool contract address."""
        pass
    
    @property
    @abstractmethod
    def token0(self) -> str:
        """Get the address of token0."""
        pass
    
    @property
    @abstractmethod
    def token1(self) -> str:
        """Get the address of token1."""
        pass
    
    @property
    @abstractmethod
    def fee(self) -> float:
        """Get the fee as a decimal (e.g., 0.003 for 0.3%)."""
        pass

    @property
    @abstractmethod
    def decimals0(self) -> int:
        """Get token0 decimal number."""
        pass

    @property
    @abstractmethod
    def decimals1(self) -> int:
        """Get token1 decimal number."""
        pass


class IV2Pool(IPool):
    """Interface for Uniswap V2-style pools."""
    
    @property
    @abstractmethod
    def reserve0(self) -> int:
        """Get the reserve of token0 in wei units."""
        pass
    
    @property
    @abstractmethod
    def reserve1(self) -> int:
        """Get the reserve of token1 in wei units."""
        pass