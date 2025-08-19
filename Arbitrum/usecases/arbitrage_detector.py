from typing import List, Optional, Dict, Any, Set, Tuple
from decimal import Decimal
import networkx as nx
import math
import asyncio
import time
from logger import logger

from infrastructure.data_providers.graph.edge import Edge
from infrastructure.data_providers.graph.cycle import Cycle
from domain.entities.models import DexTradingPair, TradingPairFilter
from domain.interfaces.market_data_provider import MarketDataProvider
from usecases.pool_simulator_manager import PoolSimulatorManager


class ArbitrageDetector:
    def __init__(
            self,
            market_data_providers: Dict[str, MarketDataProvider]
    ):
        self.market_data_providers = market_data_providers
        self.price_graph = nx.MultiDiGraph()
        self.pool_simulator_manager = PoolSimulatorManager()

        self.cycle_cache: Dict[str, Cycle] = {}
        # TODO: Add Cycle Class
    
    def _is_v2_provider(self, provider_name: str) -> bool:
        """
        Check if the provider is a Uniswap V2 or Pancake V2 provider.
        
        Args:
            provider_name: Name of the provider
            
        Returns:
            True if it's a V2 provider, False otherwise
        """
        return provider_name in ['uniswap_v2', 'pancakeswap_v2', 'sushiswap_v2', 'fraxswap_v2', 'shibaswap_v2']

    async def _add_pairs_to_graph_parallel(self, pairs: List[DexTradingPair], provider_name: str, thread_count: int):
        if not pairs:
            logger.debug(f"No pairs to add from {provider_name}")
            return
        
        # Create a lock for thread safety when modifying the graph
        graph_lock = asyncio.Lock()

        # Process a chunk of pairs:
        async def process_pairs_chunk(chunk):
            v2_pool_simulators = []

            for pair in chunk:
                try:
                    if not isinstance(pair, DexTradingPair):
                        continue

                    async with graph_lock:
                        token0_address = pair.token0_address
                        token1_address = pair.token1_address

                        # TODO: Check the self.ETH_USD_PRICE
                        if not self.price_graph.has_node(token0_address):
                            self.price_graph.add_node(
                                token0_address, 
                                symbol=pair.token0_symbol,
                                # USD_price = pair.token0_derivedETH * self.ETH_USD_PRICE,
                                decimals=pair.token0_decimals
                            )
                        
                        if not self.price_graph.has_node(token1_address):
                            self.price_graph.add_node(
                                token1_address,
                                symbol=pair.token1_symbol,
                                # USD_price = pair.token1_derivedETH * self.ETH_USD_PRICE,
                                decimals=pair.token1_decimals
                            )
                        
                        # Add edges with weight as -log(price)
                        if pair.token1_price > 0:
                            self.price_graph.add_edge(
                                u_for_edge= token0_address,
                                v_for_edge= token1_address,
                                key=pair.pair_address,
                                weight = math.log(Decimal(pair.token1_price)),
                                price = pair.token1_price,
                                provider = provider_name,
                                fee = pair.fee_tier/1000000.0  # Convert fee tier from percentage to decimal
                            )

                        if pair.token0_price > 0:
                            self.price_graph.add_edge(
                                u_for_edge= token1_address,
                                v_for_edge= token0_address,
                                key=pair.pair_address,
                                weight = math.log(Decimal(pair.token0_price)),
                                price= pair.token0_price,
                                provider=provider_name,
                                fee = pair.fee_tier/1000000.0
                            )
                except Exception as e:
                    logger.exception(f"Error processing pair")
    
                # Collect pool simulators
                if self._is_v2_provider(provider_name):
                    v2_pool_simulators.append((
                        pair.pair_address,
                        pair.token0_address,
                        pair.token1_address,
                        pair.token0_decimals,
                        pair.token1_decimals,
                        pair.reserve0,
                        pair.reserve1,
                        pair.fee_tier,
                        pair.block_number,
                        provider_name
                    ))
            
            # Add to pool simulators
            for args in v2_pool_simulators:
                await self.pool_simulator_manager.create_and_store_v2_pool_simulator(*args)
        
        chunk_size = max(1, len(pairs) // thread_count)
        chunks = [pairs[i:i + chunk_size] for i in range(0, len(pairs), chunk_size)]
        
        # Process chunks in parallel
        tasks = [process_pairs_chunk(chunk) for chunk in chunks]
        await asyncio.gather(*tasks)
    
    async def build_graph(self, limit: int = 100, thread_count: int = 4) -> None:
        self.price_graph.clear()
        self.pool_simulator_manager.clear()

        for provider_name, provider in self.market_data_providers.items():
            try:
                logger.info(f"Fetching top {limit} pairs from {provider_name}")
                
                filter_options = TradingPairFilter(
                    min_liquidity_usd = Decimal("10"),
                    min_volume_24h = None,
                    assets = None
                )
                pairs = await provider.get_all_pairs(limit=limit, filter_options=filter_options, order_by_liquidity=True)
            
                # Add pairs to graph in parallel
                await self._add_pairs_to_graph_parallel(pairs, provider_name, thread_count)
                
                logger.info(f"Successfully fetched {len(pairs)} pairs from {provider_name}")
            except Exception as e:
                logger.exception(f"Error fetching pairs from {provider_name}: {e}")


    # TODO: Update sau task 3.
    '''
    def cache_triangular_arbitrage_cycles(self) -> None:
        """
        Cache all found triangular arbitrage cycles.
        """
        try:
            for node_cycle in nx.simple_cycles(self.price_graph, 3):
                if len(node_cycle) != 3:
                    continue
                
                pairs = [[], [], []]
                
                #Add all pair addresses in a cycle to pairs list seperated by edges 
                for i in range(len(node_cycle)):
                    from_token = node_cycle[i]
                    to_token = node_cycle[(i + 1) % len(node_cycle)]
                    
                    edge_data = self.price_graph.get_edge_data(from_token, to_token)
                    if not edge_data:
                        logger.error(f"No edge data found for {from_token} -> {to_token} (CTAC)")
                        continue
                    
                    for pair_address in edge_data.keys():
                        pairs[i].append((from_token, to_token, pair_address))
                
                edge_cycles = []
                #Get all combinations of pair addresses to create all possible cycle combinations
                for first_pair in pairs[0]:
                    edge1 = self.price_graph[first_pair[0]][first_pair[1]][first_pair[2]]
                    E1 = Edge(
                        from_token=first_pair[0],
                        to_token=first_pair[1],
                        pair_address=first_pair[2],
                        weight=edge1['weight'],
                        price=edge1['price'],
                        provider=edge1['provider'],
                        fee=edge1['fee']
                    )

                    for second_pair in pairs[1]:
                        edge2 = self.price_graph[second_pair[0]][second_pair[1]][second_pair[2]]
                        E2 = Edge(
                            from_token=second_pair[0],
                            to_token=second_pair[1],
                            pair_address=second_pair[2],
                            weight=edge2['weight'],
                            price=edge2['price'],
                            provider=edge2['provider'],
                            fee=edge2['fee']
                        )

                        for third_pair in pairs[2]:
                            edge3 = self.price_graph[third_pair[0]][third_pair[1]][third_pair[2]]
                            E3 = Edge(
                                from_token=third_pair[0],
                                to_token=third_pair[1],
                                pair_address=third_pair[2],
                                weight=edge3['weight'],
                                price=edge3['price'],
                                provider=edge3['provider'],
                                fee=edge3['fee']
                            )

                            edge_cycles.append(E1, E2, E3)
                
                #Cache all cycles with key as pair address
                for edge_cycle in edge_cycles:
                    for pair_address in edge_cycle:
                        if pair_address not in self.cycle_cache.keys():
                            self.cycle_cache[pair_address] = []
                        self.cycle_cache[pair_address].append([edge_cycle, node_cycle])
                        
        except Exception as e:
            logger.error(f"Error caching arbitrage cycles: {e}")
    '''