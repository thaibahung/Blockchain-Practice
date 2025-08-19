import asyncio
from web3 import Web3
import json
import os
from logger import logger

from application.arbitrage_service import ArbitrageService
from contracts import ContractManager

# domain
from domain.entities.constants import DexName, HandlerName, Network

# usecases
from usecases.arbitrage_detector import ArbitrageDetector

# infrastructure
from infrastructure.data_providers.market_data.uniswap_v2_market_data_provider import UniswapV2MarketDataProvider
from infrastructure.data_providers.chains.arbitrum_blockchain_provider import ArbitrumBlockchainProvider

from config import (
    THEGRAPH_API_KEY, INFURA_API_KEY, UNISWAP_V2_THEGRAPH
)

async def main():
    """Main entry point for the application."""
    logger.info("Starting Arbitrum Arbitrage Detector")

    web3 = Web3(Web3.HTTPProvider(f"https://arbitrum-mainnet.infura.io/v3/{INFURA_API_KEY}"))
    logger.info(f"Connected to Arbitrum mainnet: {web3.is_connected()}")

    contract_manager = ContractManager(web3)

    blockchain_provider = ArbitrumBlockchainProvider(web3, contract_manager)

    
    uniswap_v2_market_provider = UniswapV2MarketDataProvider(
        graph_url=UNISWAP_V2_THEGRAPH,
        network=Network.ARBITRUM
    )

    arbitrage_detector = ArbitrageDetector(
        market_data_providers={
            "uniswap_v2": uniswap_v2_market_provider
        }
    )
    
    # Initialize services
    arbitrage_service = ArbitrageService(
        arbitrage_detector=arbitrage_detector,
        blockchain_provider=blockchain_provider,
        blockchain=Network.ARBITRUM
    )

    # Start monitoring mempool
    await arbitrage_service.start_monitoring()
    
if __name__ == "__main__":
    asyncio.run(main())