from abc import ABC, abstractmethod
from typing import List, Optional, Union, TypeVar, Literal, AsyncGenerator
from ..entities.models import CexTradingPair, DexTradingPair, TradingPairFilter

MarketPair = TypeVar('MarketPair', CexTradingPair, DexTradingPair)

class MarketDataProvider(ABC):
    """
    Interface for market data providers.
    Infrastructure layer must implement this interface to provide
    actual market data functionality.
    """

    @property
    @abstractmethod
    def market_id(self) -> str:
        """
        Get the unique identifier for this market.
        
        Returns:
            Market identifier string
        """
        pass

    @property
    @abstractmethod
    def market_type(self) -> Literal["Dex", "Cex"]:
        """
        Get the type of this market (DEX or CEX).
        
        Returns:
            Market type: "Dex" or "Cex"
        """
        pass

    @property
    @abstractmethod
    def amm_type(self) ->Literal["uniswap-v2", "uniswap-v3", "uniswap-v4"]:
        """
        Get AMM type of this market (uniswap-v2, uniswap-v3 or uniswap-v4).
        
        Returns:
            AMM type: "uniswap-v2", "uniswap-v3" or "uniswap-v4"
        """
        pass
    
    @abstractmethod
    async def get_all_pairs(
        self,
        limit: Optional[int] = None,
        filter_options: Optional[TradingPairFilter] = None,
        order_by_liquidity: bool = True
    ) -> List[MarketPair]:
        """
        Get all available trading pairs, optionally filtered and ordered by liquidity.
        
        Args:
            limit: Maximum number of pairs to return
            filter_options: Filter criteria for trading pairs
            order_by_liquidity: Whether to order pairs by liquidity (descending)
        
        Returns:
            List of trading pairs (CexTradingPair for CEX, DexTradingPair for DEX)
            ordered by liquidity (if order_by_liquidity is True)
        
        Example CEX usage:
            pairs = await binance_provider.get_all_pairs(
                limit=10,
                filter_options=TradingPairFilter(
                    min_liquidity_usd=1000000,
                    quote_assets=["USDT", "USDC"]
                ),
                order_by_liquidity=True
            )
        
        Example DEX usage:
            pairs = await uniswap_provider.get_all_pairs(
                limit=10,
                filter_options=TradingPairFilter(
                    min_liquidity_usd=100000,
                    min_volume_24h=50000
                ),
                order_by_liquidity=True
            )
        """
        pass