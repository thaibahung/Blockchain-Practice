import asyncio
from web3 import Web3
import json
import os
from logger import logger
import matplotlib.pyplot as plt
import networkx as nx
import csv
import decimal

from application.arbitrage_service import ArbitrageService
from contracts import ContractManager

# domain
from domain.entities.constants import DexName, HandlerName, Network

# usecases
from usecases.arbitrage_detector import ArbitrageDetector
from usecases.pool_simulator_manager import PoolSimulatorManager

# infrastructure
from infrastructure.data_providers.market_data.uniswap_v2_market_data_provider import UniswapV2MarketDataProvider
from infrastructure.data_providers.chains.arbitrum_blockchain_provider import ArbitrumBlockchainProvider

from config import (
    THEGRAPH_API_KEY, INFURA_API_KEY, UNISWAP_V2_THEGRAPH
)

# Test Function
def export_to_csv(pool_simulator_manager: PoolSimulatorManager, file_path: str) -> None:
        """
        Export all pool simulators to a CSV file with columns: address, token0, token1, reserve0, reserve1
        """
        with open(file_path, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["address", "token0", "token1", "reserve0", "reserve1", "block_number"])
            for pool in pool_simulator_manager.pool_simulators.values():
                # Assumes pool has attributes: address, token0, token1, reserve0, reserve1
                writer.writerow([
                    getattr(pool, "address", ""),
                    getattr(pool, "token0", ""),
                    getattr(pool, "token1", ""),
                    getattr(pool, "reserve0", ""),
                    getattr(pool, "reserve1", ""),
                    getattr(pool, "block_number", "")
                ])


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

        print("\n=== Arbitrage Cycles (node addresses and pair addresses) ===")
        for i, cycle in enumerate(arbitrage_service.arbitrage_detector.cycles_2):
            print(f"Cycle {i}: ")
            print(f"  token1: {cycle.token1}")
            print(f"  token2: {cycle.token2}")
            print(f"  edge1 (pair address): {cycle.edge1}")
            print(f"  edge2 (pair address): {cycle.edge2}")

        print("=== End of Cycles ===\n")

        '''
        # Debug: Print all cycles with node and edge (pair address) details
        print("\n=== Arbitrage Cycles (node addresses and pair addresses) ===")
        for i, cycle in enumerate(arbitrage_service.arbitrage_detector.cycles_3):
            print(f"Cycle {i}: ")
            print(f"  token1: {cycle.token1}")
            print(f"  token2: {cycle.token2}")
            print(f"  token3: {cycle.token3}")
            print(f"  edge1 (pair address): {cycle.edge1}")
            print(f"  edge2 (pair address): {cycle.edge2}")
            print(f"  edge3 (pair address): {cycle.edge3}")

        print("=== End of Cycles ===\n")

        # Test: Check if each token node is connected to the correct edge (pair address) in the price graph
        price_graph = arbitrage_service.arbitrage_detector.price_graph
        for i, cycle in enumerate(arbitrage_service.arbitrage_detector.cycles_3):
            # Check token1 -> token2 via edge1
            edge1_found = False
            if price_graph.has_edge(cycle.token1, cycle.token2, key=cycle.edge1):
                edge1_found = True
            # Check token2 -> token3 via edge2
            edge2_found = False
            if price_graph.has_edge(cycle.token2, cycle.token3, key=cycle.edge2):
                edge2_found = True
            # Check token3 -> token1 via edge3
            edge3_found = False
            if price_graph.has_edge(cycle.token3, cycle.token1, key=cycle.edge3):
                edge3_found = True

            print(f"Test Cycle {i}: edge1 ({cycle.token1}->{cycle.token2}, {cycle.edge1}) exists: {edge1_found}")
            print(f"Test Cycle {i}: edge2 ({cycle.token2}->{cycle.token3}, {cycle.edge2}) exists: {edge2_found}")
            print(f"Test Cycle {i}: edge3 ({cycle.token3}->{cycle.token1}, {cycle.edge3}) exists: {edge3_found}")
            if not (edge1_found and edge2_found and edge3_found):
                print(f"  [ERROR] At least one edge in cycle {i} does not exist in the price graph!")

        export_to_csv(arbitrage_service.arbitrage_detector.pool_simulator_manager, "output1.csv")
        '''


if __name__ == "__main__":
    asyncio.run(main())