import asyncio
from typing import List, Optional, Dict, Literal, Any
from domain.interfaces.blockchain_provider import IBlockchainProvider
from usecases.arbitrage_detector import ArbitrageDetector
from domain.entities.models import PoolEvent
from config import TOP_PAIRS_COUNT

from logger import logger

class ArbitrageService:
    def __init__(self, arbitrage_detector: ArbitrageDetector, blockchain_provider: IBlockchainProvider, blockchain: str = 'arbitrum'):
        self.arbitrage_detector = arbitrage_detector
        self.blockchain_provider = blockchain_provider
        self.blockchain = blockchain

        # Queue for pool updates
        self._pool_event_queue = asyncio.Queue()

        # Flag to indicate if the graph is built
        self.graph_built = False

    async def start_monitoring(self) -> None:
        logger.info("Starting arbitrage monitoring system")
        logger.info(f"Monitoring top {TOP_PAIRS_COUNT} pairs by liquidity")

        # Build the price graph
        logger.info("Building price graph from market data providers...")
        await self.arbitrage_detector.build_graph(limit=TOP_PAIRS_COUNT, thread_count=12)

        # Mark the graph as built
        self.graph_built = True
        logger.info("Price graph built")