"""
Uniswap V2 market data provider implementation using TheGraph API and Hummingbot Gateway.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, Optional, List, Literal
import logging
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
from domain.interfaces.market_data_provider import MarketDataProvider, MarketPair
from domain.entities.models import DexTradingPair, TradingPairFilter
from .graphql.uniswap_v2_queries import (
    GET_TOP_PAIRS
)

from config import UNISWAP_V2_THEGRAPH
from logger import logger

class UniswapV2MarketDataProvider(MarketDataProvider):
    def __init__(self, graph_url: str, network: str):
        self._market_id = f"uniswap_v2-{network}"
        self._market_type: Literal["Dex", "Cex"] = "Dex"  

        # Initialize GraphQL client with timeout
        self._transport = AIOHTTPTransport(
            url=graph_url,
            timeout=30  # 30 seconds timeout
        )
        self._graph_client = Client(
            transport=self._transport,
            fetch_schema_from_transport=True
        )
        self._network = network
        # Cache for token and pair data
        self._pair_cache: Dict[str, Dict] = {}

    @property
    def market_id(self) -> str:
        """Get the unique identifier for this market."""
        return self._market_id

    @property
    def market_type(self) -> Literal["Dex", "Cex"]:
        """Get the type of this market (DEX or CEX)."""
        return self._market_type
    
    @property
    def amm_type(self) -> Literal["uniswap-v2", "uniswap-v3", "uniswap-v4"]:
        """Get AMM type of this market (uniswap-v2, uniswap-v3 or uniswap-v4)."""
        return "uniswap-v2"
    
    async def get_all_pairs(
        self,
        limit: Optional[int] = None,
        filter_options: Optional[TradingPairFilter] = None,
        order_by_liquidity: bool = True
    ) -> List[MarketPair]:
        """
        Get all available trading pairs using TheGraph API.
        
        Args:
            limit: Maximum number of pairs to return
            filter_options: Filter criteria for trading pairs
            order_by_liquidity: Whether to order pairs by liquidity (descending)
        
        Returns:
            List of DexTradingPair objects
        """   
        try:
            # Prepare GraphQL query
            yesterday_utc  = datetime.now(timezone.utc) - timedelta(days=1)
            variables = {
                "first": limit or 1000,
                "minLiquidityUSD": str(
                    filter_options.min_liquidity_usd if filter_options and filter_options.min_liquidity_usd
                    else 0
                ),
                "lastTransactionTimestamp": int(yesterday_utc.timestamp())
            }
            
            # Execute query
            async with self._graph_client as session:
                result = await session.execute(
                    gql(GET_TOP_PAIRS),
                    variable_values=variables
                )
            current_block_number = int(result["_meta"]["block"]["number"])
            pairs = []
            for pair_data in result["pairs"]:
                # Apply additional filters
                if filter_options:
                    if filter_options.min_volume_24h:
                        if Decimal(pair_data["volumeUSD"]) < filter_options.min_volume_24h:
                            continue
                    
                    if filter_options.assets:
                        if pair_data["token0"]["symbol"] not in filter_options.assets and \
                           pair_data["token1"]["symbol"] not in filter_options.assets:
                            continue
                
                # Create DexTradingPair object with both prices
                pair = DexTradingPair(
                    pair_address=pair_data["id"],
                    token0_address=pair_data["token0"]["id"],
                    token0_symbol=pair_data["token0"]["symbol"],
                    token0_derivedETH=Decimal(pair_data["token0"]["derivedETH"]),
                    token0_decimals=int(pair_data["token0"]["decimals"]),
                    token1_address=pair_data["token1"]["id"],
                    token1_symbol=pair_data["token1"]["symbol"],
                    token1_derivedETH=Decimal(pair_data["token1"]["derivedETH"]),
                    token1_decimals=int(pair_data["token1"]["decimals"]),
                    total_liquidity_usd=Decimal(pair_data["reserveUSD"]),
                    volume_24h=Decimal(pair_data["volumeUSD"]),
                    fee_tier=3000,  # 0.3% for Uniswap V2
                    reserve0=Decimal(pair_data["reserve0"]),
                    reserve1=Decimal(pair_data["reserve1"]),
                    token0_price=Decimal(pair_data["token0Price"]),  # Price of token0 in terms of token1
                    token1_price=Decimal(pair_data["token1Price"]),   # Price of token1 in terms of token0,
                    block_number=current_block_number,
                    network=self._network
                )
                pairs.append(pair)
            
            # Sort by liquidity if requested
            if order_by_liquidity:
                pairs.sort(key=lambda x: x.total_liquidity_usd, reverse=True)
            
            return pairs
            
        except Exception as e:
            logger.exception(f"Failed to get trading pairs from Uniswap V2")
            raise
    
    async def close(self) -> None:
        """Close connections and cleanup."""
        await self._transport.close()
        logger.info("Uniswap V2 market data provider closed")